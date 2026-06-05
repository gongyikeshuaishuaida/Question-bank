const state = {
  metadata: null,
  questions: [],
  selected: new Map(),
  currentQuestion: null,
  currentImport: null,
  currentDraft: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = await response.text();
    try {
      detail = JSON.parse(detail).detail;
    } catch (_) {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (options.rawText) return response.text();
  return response.json();
}

function optionList(select, values, allLabel) {
  select.innerHTML = "";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = allLabel;
  select.appendChild(all);
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

async function loadMetadata() {
  state.metadata = await api("/api/metadata");
  $("metaLine").textContent = `${state.metadata.count} 道题 · ${state.metadata.papers.length} 份试卷 · ${state.metadata.knowledge.length} 个知识点`;
  optionList($("paperFilter"), state.metadata.papers, "全部试卷");
  optionList($("knowledgeFilter"), state.metadata.knowledge, "全部知识点");
  optionList($("typeFilter"), state.metadata.types, "全部题型");
  optionList($("statusFilter"), state.metadata.statuses, "全部状态");

  const knowledgeSelect = document.querySelector("#draftForm select[name='knowledge']");
  knowledgeSelect.innerHTML = "";
  state.metadata.knowledge.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    knowledgeSelect.appendChild(option);
  });
}

function queryParams() {
  const params = new URLSearchParams();
  const pairs = [
    ["paper", $("paperFilter").value],
    ["knowledge", $("knowledgeFilter").value],
    ["type", $("typeFilter").value],
    ["status", $("statusFilter").value],
    ["q", $("searchBox").value.trim()],
  ];
  pairs.forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return params.toString();
}

async function loadQuestions() {
  const qs = queryParams();
  state.questions = await api(`/api/questions${qs ? `?${qs}` : ""}`);
  $("resultCount").textContent = `${state.questions.length} 题`;
  renderQuestionList();
}

function renderQuestionList() {
  const list = $("questionList");
  list.innerHTML = "";
  state.questions.forEach((question) => {
    const row = document.createElement("div");
    row.className = `question-item ${state.currentQuestion?.id === question.id ? "active" : ""}`;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = state.selected.has(question.id);
    checkbox.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleSelected(question);
    });

    const body = document.createElement("div");
    body.innerHTML = `
      <div class="question-id">${question.id}</div>
      <div>${escapeHtml(question.excerpt || question.title)}</div>
      <div class="question-meta">${question.type || ""} · ${question.difficulty || ""} · ${question.status || ""}<br>${question.knowledge.join(" / ")}</div>
    `;
    row.append(checkbox, body);
    row.addEventListener("click", () => openQuestion(question.id));
    list.appendChild(row);
  });
}

async function openQuestion(id) {
  const detail = await api(`/api/questions/${encodeURIComponent(id)}`);
  state.currentQuestion = detail;
  $("detailEmpty").classList.add("hidden");
  $("questionDetail").classList.remove("hidden");
  $("progressPanel").classList.remove("hidden");
  $("questionDetail").innerHTML = `
    <div class="question-meta">${detail.paper} · 第 ${detail.number} 题 · ${detail.knowledge.join(" / ")}</div>
    ${detail.html}
    <h2>答案</h2>
    ${detail.answer_html || "<p>未填写</p>"}
    <h2>解析</h2>
    ${detail.analysis_html || "<p>未填写</p>"}
  `;
  $("progressStatus").value = detail.status || "未练习";
  $("progressCount").value = detail.completed_count ?? 0;
  $("progressAccuracy").value = detail.accuracy ?? "";
  $("mistakeReason").value = detail.meta["错题原因"] ?? "";
  renderQuestionList();
}

async function saveProgress() {
  if (!state.currentQuestion) return;
  const payload = {
    状态: $("progressStatus").value,
    完成次数: Number($("progressCount").value || 0),
    正确率: $("progressAccuracy").value,
    错题原因: $("mistakeReason").value,
  };
  const updated = await api(`/api/questions/${encodeURIComponent(state.currentQuestion.id)}/progress`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.currentQuestion = updated;
  await loadMetadata();
  await loadQuestions();
}

function toggleSelected(question) {
  if (state.selected.has(question.id)) state.selected.delete(question.id);
  else state.selected.set(question.id, question);
  renderSelected();
  renderQuestionList();
}

function renderSelected() {
  $("selectedCount").textContent = state.selected.size;
  const list = $("selectedList");
  list.innerHTML = "";
  state.selected.forEach((question) => {
    const chip = document.createElement("div");
    chip.className = "selected-chip";
    chip.innerHTML = `<span>${question.id}</span>`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "移除";
    remove.addEventListener("click", () => {
      state.selected.delete(question.id);
      renderSelected();
      renderQuestionList();
    });
    chip.appendChild(remove);
    list.appendChild(chip);
  });
}

async function exportSet() {
  const ids = [...state.selected.keys()];
  if (!ids.length) return;
  const markdown = await api("/api/sets/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ids,
      include_answers: $("includeAnswers").checked,
      title: "练习卷",
    }),
    rawText: true,
  });
  $("exportOutput").value = markdown;
}

async function submitImport(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  data.set("force_ocr", form.force_ocr.checked ? "true" : "false");
  $("importStatus").textContent = "处理中";
  $("commitImportBtn").disabled = true;
  try {
    state.currentImport = await api("/api/imports", { method: "POST", body: data });
    $("importStatus").textContent = `${state.currentImport.drafts.length} 条草稿`;
    $("commitImportBtn").disabled = false;
    renderImport();
  } catch (error) {
    $("importStatus").textContent = `失败：${error.message}`;
  }
}

function renderImport() {
  renderPages();
  renderDraftList();
}

function renderPages() {
  const list = $("pageList");
  list.innerHTML = "";
  if (!state.currentImport) return;
  state.currentImport.pages.forEach((page) => {
    const card = document.createElement("div");
    card.className = "page-card";
    card.innerHTML = `
      <strong>第 ${page.page} 页</strong>
      <img src="/vault/${page.image}" alt="第 ${page.page} 页">
      <div class="ocr-text">${escapeHtml(page.ocr_error || "")}${page.ocr_error ? "\n\n" : ""}${escapeHtml(page.ocr_text || "")}</div>
    `;
    list.appendChild(card);
  });
}

function renderDraftList() {
  const list = $("draftList");
  list.innerHTML = "";
  if (!state.currentImport) return;
  state.currentImport.drafts.forEach((draft) => {
    const row = document.createElement("div");
    row.className = `draft-item ${state.currentDraft?.id === draft.id ? "active" : ""}`;
    const check = document.createElement("input");
    check.type = "checkbox";
    check.checked = draft.accepted;
    check.addEventListener("click", async (event) => {
      event.stopPropagation();
      draft.accepted = check.checked;
      await updateDraft(draft, { accepted: check.checked }, false);
    });
    const body = document.createElement("div");
    body.innerHTML = `
      <div class="draft-id">第 ${draft.number} 题 · ${draft.question_type}</div>
      <div>${escapeHtml((draft.body || "").replace(/^#.+\\n/, "").slice(0, 120))}</div>
      <div class="draft-meta">${(draft.knowledge || []).join(" / ")} · ${draft.image_check || ""}</div>
    `;
    row.append(check, body);
    row.addEventListener("click", () => openDraft(draft.id));
    list.appendChild(row);
  });
}

function openDraft(id) {
  const draft = state.currentImport.drafts.find((item) => item.id === id);
  if (!draft) return;
  state.currentDraft = draft;
  $("draftEmpty").classList.add("hidden");
  $("draftForm").classList.remove("hidden");
  const form = $("draftForm");
  form.number.value = draft.number || "";
  form.question_type.value = draft.question_type || "选择题";
  form.difficulty.value = draft.difficulty || "中等";
  [...form.knowledge.options].forEach((option) => {
    option.selected = (draft.knowledge || []).includes(option.value);
  });
  form.body.value = draft.body || "";
  form.answer.value = draft.answer || "";
  form.analysis.value = draft.analysis || "";
  form.image_check.value = draft.image_check || "无图片";
  form.accepted.checked = Boolean(draft.accepted);
  form.cropPage.value = "";
  form.cropBox.value = "";
  form.cropLabel.value = "";
  renderCropList();
  renderDraftList();
}

function draftPayloadFromForm() {
  const form = $("draftForm");
  return {
    number: form.number.value.trim(),
    question_type: form.question_type.value,
    difficulty: form.difficulty.value,
    knowledge: [...form.knowledge.selectedOptions].map((option) => option.value),
    body: form.body.value,
    answer: form.answer.value,
    analysis: form.analysis.value,
    image_check: form.image_check.value,
    accepted: form.accepted.checked,
    images: state.currentDraft.images || [],
  };
}

async function saveDraft(event) {
  event.preventDefault();
  if (!state.currentDraft) return;
  await updateDraft(state.currentDraft, draftPayloadFromForm(), true);
}

async function updateDraft(draft, payload, rerender) {
  const updated = await api(`/api/imports/${state.currentImport.id}/drafts/${draft.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const index = state.currentImport.drafts.findIndex((item) => item.id === draft.id);
  state.currentImport.drafts[index] = updated;
  state.currentDraft = updated;
  if (rerender) {
    openDraft(updated.id);
  } else {
    renderDraftList();
  }
}

function addCrop() {
  if (!state.currentDraft) return;
  const form = $("draftForm");
  const box = form.cropBox.value.split(",").map((value) => Number(value.trim()));
  if (box.length !== 4 || box.some((value) => Number.isNaN(value))) return;
  state.currentDraft.images = state.currentDraft.images || [];
  state.currentDraft.images.push({
    page: Number(form.cropPage.value || 1),
    box,
    label: form.cropLabel.value || `图${state.currentDraft.images.length + 1}`,
  });
  renderCropList();
}

function renderCropList() {
  const list = $("cropList");
  if (!state.currentDraft?.images?.length) {
    list.textContent = "未加入裁图";
    return;
  }
  list.innerHTML = state.currentDraft.images
    .map((item, index) => `#${index + 1} 第 ${item.page} 页 [${item.box.join(", ")}] ${escapeHtml(item.label || "")}`)
    .join("<br>");
}

async function commitImport() {
  if (!state.currentImport) return;
  $("importStatus").textContent = "提交中";
  try {
    const result = await api(`/api/imports/${state.currentImport.id}/commit`, { method: "POST" });
    $("importStatus").textContent = `写入 ${result.written.length} 个文件`;
    await loadMetadata();
    await loadQuestions();
  } catch (error) {
    $("importStatus").textContent = `提交失败：${error.message}`;
  }
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      $(`${tab.dataset.view}View`).classList.add("active");
    });
  });
  ["paperFilter", "knowledgeFilter", "typeFilter", "statusFilter"].forEach((id) => {
    $(id).addEventListener("change", loadQuestions);
  });
  $("searchBox").addEventListener("input", debounce(loadQuestions, 220));
  $("reloadBtn").addEventListener("click", async () => {
    await loadMetadata();
    await loadQuestions();
  });
  $("saveProgressBtn").addEventListener("click", saveProgress);
  $("clearSelectedBtn").addEventListener("click", () => {
    state.selected.clear();
    renderSelected();
    renderQuestionList();
  });
  $("exportBtn").addEventListener("click", exportSet);
  $("importForm").addEventListener("submit", submitImport);
  $("draftForm").addEventListener("submit", saveDraft);
  $("addCropBtn").addEventListener("click", addCrop);
  $("commitImportBtn").addEventListener("click", commitImport);
}

function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function boot() {
  bindEvents();
  await loadMetadata();
  await loadQuestions();
  renderSelected();
}

boot().catch((error) => {
  $("metaLine").textContent = `启动失败：${error.message}`;
});

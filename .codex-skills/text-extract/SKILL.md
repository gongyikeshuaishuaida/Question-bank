---
name: text-extract
description: Process Chinese information technology exam PDFs into an Obsidian question bank. Use when the user provides exam PDF originals, answer PDFs, or asks to extract, organize, validate, update, or import practice statistics for IT exam questions in an Obsidian vault with files such as 题库管理规则.md, 题库_模板.md, 题库管理.base, PDF试卷提取方案.md, 试卷/, and attachments/.
---

# Text Extract

## Overview

Extract only the information technology part of a Chinese exam PDF into the user's Obsidian question bank, following the vault's local management rules exactly. Preserve original question wording, create stable question notes, crop only local question images, and write answers and explanations during extraction.

## Required Context

Before processing, read the vault-local rules instead of relying on memory:

- `题库管理规则.md`
- `题库_模板.md`
- `题库管理.base`
- `PDF试卷提取方案.md`
- Existing extracted notes for the same paper, if any

Use the current rule files as authoritative when they differ from this skill.

## Helper Scripts

This skill includes reusable scripts under `scripts/`. Prefer these for the repeatable mechanical parts of extraction, then do the question splitting, answer checking, and explanation writing according to the vault-local rules.

Use `py -X utf8` on Windows to avoid Chinese path/output encoding issues.

### Render PDF Pages

Render selected pages to PNG files before cropping local question images:

```powershell
py -X utf8 <skill_dir>/scripts/render_pdf_pages.py "试卷/YYYYMM-组织-类型.pdf" --pages 1-7 --prefix paper --out-dir _pdf_pages
```

The `--pages` argument accepts page lists and ranges such as `1-7,10`. The output files are named like `_pdf_pages/paper_p02.png`.

### Crop Question Images

Create a JSON crop spec and crop only the local image needed by each question:

```json
[
  {
    "label": "q07 flowchart",
    "source": "_pdf_pages/paper_p02.png",
    "box": [845, 535, 1145, 915],
    "output": "attachments/YYYYMM组织_07_图1.png"
  }
]
```

Run:

```powershell
py -X utf8 <skill_dir>/scripts/crop_question_images.py crops.json
```

The crop box is `[left, top, right, bottom]` in rendered PNG pixels. Manually inspect every cropped image after running; remove neighboring题干、选项、页脚、图号外的无关内容 where possible. A checked example is available at `scripts/examples/202604-jinhua-crops.example.json`.

### Validate Generated Notes

Run validation before finishing:

```powershell
py -X utf8 <skill_dir>/scripts/validate_question_bank.py --prefix YYYYMM-组织-类型
```

The validator checks filename/id consistency, required frontmatter fields, stale fields, non-empty answer/analysis sections, image status consistency, and missing Obsidian attachment references.

## Workflow

1. Identify the paper metadata.
   - Use `YYYYMM-组织-类型` as the paper prefix, for example `202604-湖衢丽-期中`.
   - Valid paper types are `期中`, `期末`, `月考`, `期初`.
   - Store PDF originals under `试卷/` as `YYYYMM-组织-类型.pdf`.
   - If an answer PDF is provided, store it as `YYYYMM-组织-类型-答案.pdf`.

2. Extract only the information technology section.
   - Do not extract general technology questions.
   - Keep question text, code, options, numbering, and materials faithful to the original.
   - Convert code to fenced `python` blocks when reliable.
   - Use inline code for expressions such as `a[i]`, `df["列名"]`, `==`, `[]`, and `()`.

3. Split notes by question id.
   - Every question note filename must equal the frontmatter `id`: `YYYYMM-组织-类型-题号.md`.
   - Use two-digit question numbers such as `01`, `09`, `15`.
   - Put each note into the folder matching its primary knowledge point.
   - Keep cross-topic knowledge points in the `知识点` list.

4. Handle material question groups.
   - If one material block supports multiple questions, include the complete material and the complete related question group in each generated note.
   - Duplicate the note once per related question.
   - Change only `id`, filename, title question number, primary classification, and the answer/explanation focus for each duplicate.

5. Use the current template fields.
   - `题型` is only `选择题` or `填空题`.
   - Do not include `分值`.
   - `来源` must link to the PDF original in `试卷/`.
   - New questions start with `完成次数: 0`, blank `正确率:`, `状态: 未练习`, blank `错题原因:`.
   - Do not add `正确次数`, `下次复习`, or `上次练习`.
   - Include tags for `题库/信息技术`, `题型/...`, `状态/...`, and primary `知识点/...`.

6. Extract images conservatively.
   - Save images under `attachments/`.
   - Use Obsidian embeds: `![[attachments/图片名.png]]`.
   - Use `scripts/render_pdf_pages.py` and `scripts/crop_question_images.py` for repeatable rendering/cropping when local dependencies are available.
   - Crop only the local image needed by the question, such as a flowchart, tree, chart, table, or option image.
   - Never save a full-page screenshot as a question image.
   - Do not add captions such as `> 上图：...` below images.
   - Set `图片核验: 待核验` after automatic extraction; change to `已通过` only after manually checking crop range, clarity, and question match.
   - Use `图片核验: 无图片` for notes without images.

7. Write answers and explanations.
   - Every note must contain `## 答案` and `## 解析`.
   - Fill answers and explanations during extraction; do not leave `待补充`.
   - Use the answer PDF when provided.
   - If no answer is provided, solve from the question content and make the reasoning explicit.
   - Selection answer format: `**正确答案：** A`.
   - Multi-answer fill-in content may use `① ...；② ...`.
   - Explain the decisive concept, elimination reason, calculation, or code trace.

8. Update management surfaces when fields change.
   - Keep `题库管理规则.md`, `题库_模板.md`, `题库管理.base`, and `Dataview查询示例.md` aligned.
   - If importing practice statistics, write `完成次数`, `正确率`, and `状态` directly into frontmatter.
   - For completed choice-question imports, set `完成次数: 1`, `状态: 已完成`, and `正确率` from the provided table.

## Validation Checklist

Run targeted checks before finishing:

- Confirm no stale fields remain if the schema changed: `正确次数`, `下次复习`, `上次练习`.
- Confirm all extracted filenames match their `id`.
- Confirm every note has `题型`, `来源`, `试卷`, `题号`, `知识点`, `完成次数`, `正确率`, `状态`, `图片核验`, and `tags`.
- Confirm each note has non-empty `## 答案` and `## 解析`.
- Confirm image notes embed only local question images and have correct `图片核验`.
- Confirm `题库管理.base` references only existing frontmatter fields or defined formulas.

Useful PowerShell checks:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
rg -n "正确次数|下次复习|上次练习" -g "*.md" -g "*.base"
rg -n "图片核验: 待核验|!\\[\\[attachments/" -g "*.md"
py -X utf8 <skill_dir>/scripts/validate_question_bank.py --prefix YYYYMM-组织-类型
```

## Response Pattern

When done, report:

- Number of question notes created or updated.
- PDF originals copied into `试卷/`.
- Images created or fixed, with their verification status.
- Any rule, template, Base, or Dataview files changed.
- Any validation that could not be completed.

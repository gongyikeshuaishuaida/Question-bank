#!/usr/bin/env python3
"""Quality checks for the current regenerated exam batch."""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "_extracted" / "current_batch_quality_report.md"


def load_regen():
    path = ROOT / "scripts" / "regenerate_current_batch_final.py"
    spec = importlib.util.spec_from_file_location("regen_current_batch", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load regenerate_current_batch_final.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regen_current_batch"] = mod
    spec.loader.exec_module(mod)
    return mod


def read_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "-", "\t")):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta


def body_section(text: str) -> str:
    m = re.search(r"^# 题目 \d{2}\s*$", text, re.M)
    a = re.search(r"^## 答案\s*$", text, re.M)
    if not m or not a or a.start() <= m.end():
        return ""
    return text[m.end():a.start()].strip()


def strip_code_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def main() -> int:
    regen = load_regen()
    prefixes = [paper.prefix for paper in regen.PAPERS]
    expected = {paper.prefix: paper.q_count for paper in regen.PAPERS}
    notes: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(path.name.startswith(prefix + "-") for prefix in prefixes):
            notes.append(path)
    notes.sort()

    issues: dict[Path, list[str]] = defaultdict(list)
    by_stem: dict[str, list[Path]] = defaultdict(list)
    by_prefix: dict[str, list[Path]] = defaultdict(list)

    classic_mojibake = re.compile(r"[锛绔涓閫鍥堟棤寰楁嫨]")
    ocr_noise = re.compile(r"笫|肘|娈|罡|揄|僖|囝|魉|匦|商三|商二|忤|枧|霎求|硭|龆|屙|卜列|下娈")
    mixed = re.compile(r"考生须知|答题前|第二部分\s*通用技术|通用技术学科|三、选择题|高[一二三]通用技术")
    placeholder = re.compile(r"按答案卷|OCR|待补充|未能完整|对应题号填写")

    for path in notes:
        by_stem[path.stem].append(path)
        for prefix in prefixes:
            if path.name.startswith(prefix + "-"):
                by_prefix[prefix].append(path)
                break

        text = path.read_text(encoding="utf-8", errors="replace")
        meta = read_frontmatter(text)
        body = body_section(text)
        body_no_code = strip_code_blocks(body)

        if not meta:
            issues[path].append("缺少 frontmatter")
        if len(body) < 80:
            issues[path].append(f"正文过短/疑似空文档，正文长度 {len(body)}")
        if classic_mojibake.search(text):
            issues[path].append("存在典型编码乱码字符")
        if ocr_noise.search(body_no_code):
            issues[path].append("存在明显 OCR 乱码/错字")
        if mixed.search(body_no_code):
            issues[path].append("混入卷头或通用技术内容")
        if placeholder.search(text):
            issues[path].append("答案或正文仍有占位/待核对文字")

        q_type = meta.get("题型", "")
        if q_type == "选择题":
            opts = set(re.findall(r"(?m)^\s*(?:- )?([ABCD])[\.．、]", body))
            if len(opts) < 4:
                issues[path].append(f"选择题选项不足，识别到 {''.join(sorted(opts)) or '无'}")
        if re.search(r"第\s*\d+\s*题图", body) and "![[" not in body:
            issues[path].append("正文提到题图但未插入图片")
        if re.search(r"(?m)^\s*(def |import |for |while |if |elif |else:|return |print\()", body_no_code):
            issues[path].append("疑似 Python 代码未放入 fenced code block")
        if re.search(r"(?m)^\s*1[6-9][\.．、]", body_no_code) or re.search(r"(?m)^\s*[23]\d[\.．、]", body_no_code):
            issues[path].append("正文疑似混入信息技术范围外题号")

    global_issues: list[str] = []
    for stem, paths in sorted(by_stem.items()):
        if len(paths) > 1:
            global_issues.append("重复题目文件: " + stem + " -> " + "；".join(str(p.relative_to(ROOT)) for p in paths))
    for prefix, count in expected.items():
        actual = len(by_prefix.get(prefix, []))
        if actual != count:
            global_issues.append(f"{prefix}: 期望 {count} 个 md，实际 {actual} 个")

    lines = ["# 当前批次质量检查报告", ""]
    lines.append(f"- 检查文件数：{len(notes)}")
    lines.append(f"- 全局问题数：{len(global_issues)}")
    lines.append(f"- 有问题文件数：{len(issues)}")
    lines.append("")
    if global_issues:
        lines += ["## 全局问题", ""]
        lines += [f"- {x}" for x in global_issues]
        lines.append("")
    lines += ["## 文件问题", ""]
    if not issues:
        lines.append("- 未发现专项检查问题。")
    else:
        for path in sorted(issues):
            lines.append(f"### {path.relative_to(ROOT).as_posix()}")
            for item in issues[path]:
                lines.append(f"- {item}")
            lines.append("")
    REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"checked {len(notes)} note(s)")
    print(f"global issues {len(global_issues)}")
    print(f"files with issues {len(issues)}")
    print(REPORT.relative_to(ROOT))
    return 1 if global_issues or issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

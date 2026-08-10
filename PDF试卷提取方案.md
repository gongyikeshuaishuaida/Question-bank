---
title: PDF试卷提取方案
type: guide
---

# PDF 试卷提取方案

本文只保留 PDF 试卷入库的流程概览。具体字段、命名、分类、图片核验、材料题处理和 Markdown 格式规则，以 [[题库管理规则]] 为准。

## 目标

把试卷 PDF 中的信息技术部分整理为符合 [[题库_模板]] 的题目 note，并完成答案、解析、图片引用和核验页更新。

## 执行入口

正式入库优先使用 `text-extract` skill 中的 MinerU 高精度模式做首轮提取：

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
py -X utf8 scripts/mineru_extract.py "试卷/YYYYMM-组织-年级-类型.pdf"
```

该脚本默认向 MinerU 传递 `--table=false`，关闭表格识别。表格数据不读取、不转写，后续直接从原 PDF 完整裁切为图片。

Flash 模式仅用于快速试跑或无图粗提，不作为含图试卷的最终导入依据：

```powershell
py -X utf8 scripts/mineru_extract.py "试卷/YYYYMM-组织-年级-类型.pdf" --flash
```

MinerU 输出只能作为初稿。最终题目必须对照原 PDF 重排题干、选项、小问、代码块、表格图片和其它图片位置。

## 流程

```text
试卷 PDF
  -> MinerU 首轮提取文字和图片
  -> 对照原 PDF 识别信息技术部分和题目边界
  -> 按题库管理规则拆分为单题 note
  -> 补全 frontmatter、答案、解析、相关链接
  -> 将局部题图复制到 attachments/ 并嵌入对应题干位置
  -> 更新 图片核验.md 和 题目核验.md
  -> 运行 scripts/validate_question_bank.py
```

## 人工核验

- 题目只提取信息技术部分，不提取通用技术部分。
- 题干、代码、选项、小问和材料题边界必须对照原 PDF 检查，不能直接粘贴 MinerU/OCR 原始输出。
- 连续程序中的三引号字符串/注释、主体代码和末尾输出语句必须完整保留在同一个 `python` 代码块中。
- `①`、`②`、`③` 等填空编号必须统一写在左右两段横线之间，例如 `______①______`；题干中含 `_`、`*`、`[]`、`/` 等 Markdown 敏感代码符号的相关内容必须用行内代码包裹。
- 题目正文开头不重复原卷题号；题号只保留在 frontmatter、文件名和一级标题中。
- 表格数据一律从原 PDF 完整裁切为图片，不读取、不转写、不重建为 Markdown/HTML 表格或普通文本。
- 材料选择题的每个 note 都保留完整公共材料，但正文只保留当前题号的一道选择题及其选项；同题组其它小题只通过 `## 相关链接` 互相链接。
- 图片必须是题目对应的局部图；整页截图、错位图片、漏边图片、堆到正文末尾的图片都不能标为 `已通过`。
- MinerU 已提取出可用分图时不强制拼图；需要手工重裁的同排多图优先整行截取，并检查下边界、边框、标签、箭头、坐标轴、图例和图注完整。
- 代码不能因 MinerU 以图片形式输出或版式识别失败而缺失：可可靠识别时转为 `python` 代码块，否则保留清晰的局部代码截图。
- 含图题默认 `图片核验: 待核验`，人工确认裁切范围、清晰度和题目对应关系后才能改为 `已通过`。
- 同一轮连续处理任务中，`图片核验.md` 和 `题目核验.md` 必须累计保留本轮全部已处理试卷；只能在开始新一轮任务时清空上一轮内容一次，不能每处理一份就覆盖。

## 校验

完成后运行仓库内 validator：

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
py -X utf8 scripts/validate_question_bank.py --prefix "YYYYMM-组织-年级-类型"
```

必要时再运行全量校验：

```powershell
py -X utf8 scripts/validate_question_bank.py --root .
```

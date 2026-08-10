# 扫描卷图片处理流程

本文档说明在题库导入扫描版试卷时，如何处理题图、表格、流程图、树图、链表图、代码截图等图片内容。目标是让题目 Markdown 中的图片清晰、完整、可追溯，并且避免漏裁边缘或裁进无关题目。

## 总体原则

扫描卷中的题图通常没有可直接提取的矢量对象，也不能完全依赖 OCR。处理原则如下：

1. 先把 PDF 页面渲染成高清整页 PNG。
2. 在整页 PNG 上确定题图边界。
3. 用 JSON 记录裁剪坐标。
4. 用脚本裁剪到 `attachments/`。
5. 人工打开裁图进行视觉核验。
6. 通过后才在题目和 `图片核验.md` 中标记图片已通过。

不要先截低清图再放大。应先高清渲染整页，再从高清页图中裁局部题图。

## 目录约定

本仓库中图片处理相关目录通常如下：

```text
试卷/                         原始试卷 PDF 和答案 PDF
_pdf_pages/                   PDF 整页渲染后的 PNG 缓存
crop_specs/                   裁剪坐标 JSON
attachments/                  题目 Markdown 实际引用的局部图片
scripts/render_pdf_pages.py   PDF 页面渲染脚本
scripts/crop_question_images.py 裁图脚本
图片核验.md                   图片核验记录
```

推荐文件流：

```text
PDF -> _pdf_pages/整页 PNG -> crop_specs/裁剪坐标 -> attachments/局部题图 -> Markdown 图片引用
```

## 第一步：判断哪些内容需要保留为图片

以下内容应优先保留为本地裁图，而不是只转成文字：

1. 流程图、树图、图结构、链表结构、队列或栈示意图。
2. 数据表格截图，尤其是题目要求“如图所示”的表格。
3. 坐标图、统计图、柱形图、折线图、散点图。
4. 代码截图或排版复杂、OCR 容易错位的代码块。
5. OCR 后无法可靠还原空间关系的材料。
6. 题干显式引用“如图”“如下图”“图中”的内容。

普通纯文字题干、选项和解析不需要截图，应整理成 Markdown 文本。

## 第二步：高清渲染 PDF 页面

仓库脚本：

```powershell
py -X utf8 scripts\render_pdf_pages.py <PDF路径> --out-dir <输出目录> --prefix <文件名前缀> --scale 2.2
```

脚本核心逻辑使用 PyMuPDF：

```python
matrix = fitz.Matrix(scale, scale)
pix = page.get_pixmap(matrix=matrix, alpha=False)
pix.save(output)
```

`--scale` 是渲染倍率：

```text
scale 2.2  约 158 dpi，常规扫描卷够用
scale 3.0  约 216 dpi，细线图、表格线较淡时使用
scale 4.0  文件更大，只在极细图线或小字图中使用
```

在 Windows PowerShell 中，中文路径容易被终端编码影响。推荐用通配发现 PDF，不要在内联 Python 或命令里硬写中文路径。

示例：

```powershell
$pdf = Get-ChildItem .\试卷 -Filter '*金丽衢*一模.pdf' |
  Where-Object { $_.Name -notlike '*答案*' } |
  Select-Object -First 1

py -X utf8 scripts\render_pdf_pages.py $pdf.FullName `
  --out-dir _pdf_pages\202512-jinliqu `
  --prefix 202512-jinliqu `
  --scale 2.2
```

输出形如：

```text
_pdf_pages/202512-jinliqu/202512-jinliqu_p01.png
_pdf_pages/202512-jinliqu/202512-jinliqu_p02.png
```

## 第三步：确定题图边界

边界在整页 PNG 上确定。裁剪框使用 `[left, top, right, bottom]` 像素坐标。

确定边界时看以下元素：

1. 图形最外侧线条。
2. 箭头顶部、箭头尾部、连接线转折处。
3. 表格的最上、最下、最左、最右边线。
4. 表头、最后一行、最后一列。
5. 坐标轴箭头、刻度、图例、单位。
6. 图注，例如“第 7 题图”。
7. 与题干直接相关的局部说明文字。

裁剪框不要紧贴图线。一般四周保留少量空白，尤其是上方箭头、下方图注和右侧最后一列。

建议边界策略：

```text
left   比最左侧有效内容再向左留 5 到 20 像素
top    比最上侧有效内容再向上留 5 到 20 像素
right  比最右侧有效内容再向右留 5 到 20 像素
bottom 比最下侧有效内容再向下留 5 到 30 像素，图注要完整包含
```

如果原图附近有其他题目文字，优先保证不裁进无关题目。在“留白”和“不裁进别题”之间冲突时，先保证题图完整，再通过微调边界减少无关内容。

## 第四步：写裁剪规格 JSON

裁剪规格放到 `crop_specs/`，文件名建议使用 ASCII，例如：

```text
crop_specs/202512-jinliqu-shierxiao-gaosan-yimo-crops.json
```

JSON 示例：

```json
[
  {
    "label": "q07-flowchart",
    "source": "_pdf_pages/202512-jinliqu/202512-jinliqu_p02.png",
    "box": [815, 700, 1270, 1138],
    "output": "attachments/202512金丽衢_07_图1.png"
  },
  {
    "label": "q14-table",
    "source": "_pdf_pages/202512-jinliqu/202512-jinliqu_p05.png",
    "box": [715, 245, 1165, 875],
    "output": "attachments/202512金丽衢_14_图1.png"
  }
]
```

字段含义：

```text
label   便于日志识别的名称
source  已渲染的整页 PNG
box     [左, 上, 右, 下] 像素坐标
output  裁剪后输出到 attachments/ 的图片
```

## 第五步：执行裁图

运行：

```powershell
py -X utf8 scripts\crop_question_images.py crop_specs\<裁剪规格>.json
```

脚本会读取 `source`，按 `box` 裁剪，并保存到 `output`。

裁图成功不等于图片通过。脚本只负责机械裁剪，最终必须人工打开图片检查。

## 第六步：人工视觉核验

裁完后必须打开 `attachments/` 中的图片看。核验不是看文件是否存在，而是看图片是否能独立支撑题目阅读。

### 完整性检查

确认没有漏掉：

1. 图形外边框。
2. 最外侧横线、竖线、斜线。
3. 箭头尖端和箭头尾部。
4. 表格表头、最后一行、最后一列。
5. 坐标轴、刻度、图例、单位。
6. 图注。
7. 图中所有可读文字。

典型漏裁表现：

```text
箭头尖端贴着图片上边缘或被截断
表格最上方横线不完整
表格最后一列数字只剩一半
图注缺失或只剩“第 x”
坐标轴箭头不见了
流程图连接线在边缘突然断掉
```

处理方法：

```text
上边漏了  减小 top
下边漏了  增大 bottom
左边漏了  减小 left
右边漏了  增大 right
```

### 无关内容检查

确认没有明显裁进：

1. 上一题选项。
2. 下一题题干。
3. 页眉、页脚、页码。
4. 与题图无关的大段材料文字。
5. 其他题目的图注或表格边缘。

轻微扫描水印如果不影响阅读，可以保留。若水印在空白边缘且明显干扰，可只清理空白边缘；不要擦到题图线条、文字、箭头和表格内容。

典型误裁表现：

```text
图片上方出现上一题 D 选项
图片下方出现下一题题干开头
图右侧带入另一栏文字
表格旁边出现无关题号
```

处理方法：

```text
上方多余  增大 top
下方多余  减小 bottom
左侧多余  增大 left
右侧多余  减小 right
```

### 清晰度检查

确认：

1. 文字能读清。
2. 表格线能看清。
3. 流程图线条连续。
4. 图片没有被二次压缩到发糊。
5. 图片比例正常，没有横向或纵向拉伸。

如果线条变淡：

1. 先检查原始整页 PNG 中线条是否本来就淡。
2. 如果整页 PNG 清楚、裁图变差，检查是否被压缩或缩放。
3. 如果整页 PNG 也淡，用更高 `--scale` 重新渲染。
4. 不要随意二值化或锐化整张图，容易让细线断裂或文字糊成块。

### 题图匹配检查

确认图片与题目完全对应：

1. 第 7 题引用第 7 题图，不引用第 8 题图。
2. 图中题注和 Markdown 题号一致。
3. 题干说“如下图所示”时，图中包含所有需要判断的信息。
4. 同一题有多张图时，图片顺序和题干顺序一致。

## 第七步：写入 Markdown 引用

题目中使用 Obsidian 图片链接：

```markdown
![[attachments/202512金丽衢_07_图1.png]]
```

图片应放在题干相关位置，通常紧跟“如图所示”之后。

不要把题图只放在解析里。题目阅读必须能直接看到图。

## 第八步：更新图片核验状态

题目 frontmatter 中：

```yaml
图片核验: 已通过
```

没有图片的题目：

```yaml
图片核验: 无图片
```

尚未检查的题目不要标通过：

```yaml
图片核验: 待核验
```

同时更新 `图片核验.md`，记录哪些题含图片、图片是否通过、是否需要重裁。

## 第九步：最终校验

运行仓库校验：

```powershell
py -X utf8 scripts\validate_question_bank.py --root .
```

再做图片引用检查：

```powershell
@'
from pathlib import Path
import re

for md in Path(".").rglob("*.md"):
    text = md.read_text(encoding="utf-8", errors="replace")
    for link in re.findall(r"!\[\[(.*?)\]\]", text):
        if not Path(link).exists():
            print("missing image:", md, "->", link)
'@ | py -X utf8 -
```

## 常见问题与处理

### 图片线条变淡

可能原因：

1. 原 PDF 扫描本来线条淡。
2. 渲染倍率太低。
3. 裁图后被查看器缩放显示。
4. 后处理清理时擦到了线条。
5. 图片被重新压缩。

处理顺序：

1. 对比原始整页 PNG。
2. 如果整页 PNG 清楚，重新裁图。
3. 如果整页 PNG 也淡，用 `--scale 3` 重新渲染。
4. 只清理空白边缘，不碰图线和文字。

### 图片边缘被裁掉

处理：

1. 找到漏裁方向。
2. 修改 JSON 中对应坐标。
3. 重新运行裁图脚本。
4. 重新打开图片核验。

坐标调整：

```text
左边漏  left 减小
上边漏  top 减小
右边漏  right 增大
下边漏  bottom 增大
```

### 裁进了别的题

处理：

1. 找到多余内容所在方向。
2. 缩小对应边界。
3. 如果缩小会裁掉题图，优先保留题图完整。
4. 对无法避免的轻微无关内容，在核验记录中说明。

坐标调整：

```text
左边多余  left 增大
上边多余  top 增大
右边多余  right 减小
下边多余  bottom 减小
```

### 水印影响阅读

处理原则：

1. 不因水印存在就重画题图。
2. 水印不影响阅读时保留。
3. 水印在空白边缘且干扰时，可小范围清理空白区域。
4. 不清理穿过题图主体的水印，除非能确认不会破坏线条和文字。

### 中文路径导致命令失败

处理原则：

1. 使用 `py -X utf8`。
2. 在 PowerShell 中用 `Get-ChildItem` 通配发现文件。
3. 不在内联 Python 字符串里硬写中文路径。
4. 复杂逻辑写成临时脚本或仓库脚本，再传入路径参数。

推荐模式：

```powershell
$pdf = Get-ChildItem .\试卷 -Filter '*关键词*.pdf' |
  Where-Object { $_.Name -notlike '*答案*' } |
  Select-Object -First 1

py -X utf8 scripts\render_pdf_pages.py $pdf.FullName --out-dir _pdf_pages\batch --prefix batch
```

## 图片通过标准

一张题图只有同时满足以下条件，才标记为 `图片核验: 已通过`：

1. 图片文件存在。
2. Markdown 引用路径正确。
3. 图形、表格、箭头、文字、图注完整。
4. 没有裁掉关键边缘。
5. 没有明显裁进无关题目。
6. 清晰度足以读题。
7. 图片和题号匹配。
8. 题干仅靠该图片能理解“如图所示”的信息。

## 推荐工作清单

每处理一份扫描卷，按以下清单执行：

```text
[ ] 确认 PDF 是否为扫描卷或图片型 PDF
[ ] 渲染整页 PNG 到 _pdf_pages/
[ ] 找出所有需要图片保留的题号
[ ] 在整页 PNG 上确定每张图的边界
[ ] 写 crop_specs/*.json
[ ] 运行 crop_question_images.py
[ ] 打开 attachments/ 中每张裁图
[ ] 检查完整性
[ ] 检查是否裁进无关内容
[ ] 检查清晰度
[ ] 检查题号匹配
[ ] 更新题目 Markdown 图片引用
[ ] 更新 frontmatter 图片核验状态
[ ] 更新 图片核验.md
[ ] 运行 validate_question_bank.py
[ ] 检查所有图片引用文件都存在
```

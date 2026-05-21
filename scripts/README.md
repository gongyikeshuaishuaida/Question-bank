# Question Bank Helper Scripts

These scripts capture the repeatable parts of the PDF-to-question-bank workflow.

## Render PDF pages

```powershell
py -X utf8 scripts/render_pdf_pages.py "试卷/202604-金华十校-期中.pdf" --pages 1-7 --prefix jinhua --out-dir _pdf_pages
```

## Crop question images

Create a JSON crop spec:

```json
[
  {
    "label": "q07 flowchart",
    "source": "_pdf_pages/jinhua_p02.png",
    "box": [845, 535, 1145, 915],
    "output": "attachments/202604金华十校_07_图1.png"
  }
]
```

Run:

```powershell
py -X utf8 scripts/crop_question_images.py crops.json
```

The crop box is `[left, top, right, bottom]` in rendered PNG pixels.

The checked crop boxes for the 202604 Jinhua paper are saved in:

```powershell
scripts/examples/202604-jinhua-crops.example.json
```

## Validate notes

```powershell
py -X utf8 scripts/validate_question_bank.py --prefix 202604-金华十校-期中
```

The validator checks filename/id consistency, required frontmatter fields, stale fields,
answer/analysis sections, and Obsidian attachment references.

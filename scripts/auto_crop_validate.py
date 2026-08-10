#!/usr/bin/env python3
"""Self-validating iterative crop workflow for scanned exam figures.

For each figure:
1. Find caption via EasyOCR
2. Determine initial crop boundary
3. Crop → OCR-validate → fix issues → re-crop (up to 5 iterations)
4. Save final crop + crop_specs JSON
"""

import easyocr, numpy as np, cv2, json, re, sys, os
from PIL import Image
from pathlib import Path

out_dir = Path('attachments')
prefix = '202511浙东北'

reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)

def ocr_page(path):
    img = np.array(Image.open(path))
    results = reader.readtext(img)
    items = []
    for bbox, text, conf in results:
        t = text.strip()
        if conf < 0.25 or len(t) < 1:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append((t, int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), conf))
    return items

def validate_crop(crop_path):
    """Returns (is_clean, issues, crop_items)."""
    items = ocr_page(crop_path)
    img = np.array(Image.open(crop_path))
    h, w = img.shape[:2]
    issues = []

    # Only flag text that clearly belongs to ANOTHER question (not figure caption)
    # Figure captions like "第7题图" or "如图a所示" are acceptable
    other_q_kw = ['回答第', '关于该', '属于', '实现功能', '程序段', '定义以下',
                  '阅读下列', '每小题', '下列代码', '下列说法', '部分程序',
                  '程序如下', 'def ', 'print(', 'import ', '微信公众号',
                  '运行后', '输入字符串']
    for t, x0, y0, x1, y1, conf in items:
        for kw in other_q_kw:
            if kw in t:
                issues.append(('question_text', t[:60], y0))
                break

    # Check for too-blank (bad crop)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 30, 100)
    total = np.sum(edges > 0) / max(edges.size, 1)
    if total < 0.002:
        issues.append(('too_blank', round(total, 5)))

    return len(issues) == 0, issues, items

def find_boundary(page_items, cap_item, page_w, page_h):
    _, cx0, cy0, cx1, cy1, _ = cap_item
    qm = re.search(r'(\d+)', cap_item[0])
    qnum = int(qm.group(1)) if qm else None

    above = [(t, y1) for t, x0, y0, x1, y1, c in page_items if y1 < cy0 and y0 > 100]
    fig_intro = [(t, y1) for t, y1 in above if qnum and str(qnum) in t]
    top_y = max(y1 for _, y1 in fig_intro) if fig_intro else max(250, cy0 - 1200)

    below = [(t, y0) for t, x0, y0, x1, y1, c in page_items if y0 > cy1]
    next_q = []
    for t, y0 in below:
        m = re.match(r'\s*(\d+)[\.\s　]', t)
        if m and qnum and int(m.group(1)) != qnum:
            next_q.append((y0, t[:30]))
    bot_y = min(y0 for y0, _ in next_q) if next_q else cy1 + 120

    # Determine figure position: left, center, or right side of page
    cap_center_x = (cx0 + cx1) // 2
    if cap_center_x < page_w * 0.4:
        # Left-side figure: capture left portion
        fig_left = max(30, cx0 - 200)
        fig_right = min(page_w * 0.55, cx1 + 400)
    elif cap_center_x > page_w * 0.6:
        # Right-side figure: capture right portion, avoid left text
        fig_left = max(page_w * 0.45, cx0 - 200)
        fig_right = min(page_w - 30, cx1 + 200)
    else:
        # Center figure
        fig_left = max(30, cx0 - 300)
        fig_right = min(page_w - 30, cx1 + 300)

    # For multi-figure pages (Q14, Q15), be more aggressive about horizontal bounds
    # Only include text within the figure's horizontal zone when determining extent
    zone_items = [(t, x0, x1) for t, x0, y0, x1, y1, c in page_items
                  if y0 >= top_y and y1 <= bot_y
                  and x0 > fig_left - 100 and x1 < fig_right + 100]
    if zone_items:
        content_left = min(x0 for _, x0, _ in zone_items)
        content_right = max(x1 for _, _, x1 in zone_items)
        fig_left = min(fig_left, content_left)
        fig_right = max(fig_right, content_right)

    margin = 40
    left_x = max(30, int(fig_left - margin))
    top_y = max(30, top_y - margin)
    right_x = min(page_w - 30, int(fig_right + margin))
    bot_y = min(page_h - 30, bot_y + margin)
    return int(left_x), int(top_y), int(right_x), int(bot_y)

# Figures to process
figures = [
    (2, 'Q7', '第7题图'),
    (4, 'Q13', '第13题图'),
    (5, 'Q14a', '图a'),
    (5, 'Q14b', '图b'),
    (6, 'Q14c', '第14题图c'),
    (7, 'Q15a', '第15题图a'),
    (7, 'Q15b', '第15题图b'),
]

name_map = {
    'Q7': f'{prefix}_07_图1.png',
    'Q13': f'{prefix}_13_图1.png',
    'Q14a': f'{prefix}_14_图1.png',
    'Q14b': f'{prefix}_14_图2.png',
    'Q14c': f'{prefix}_14_图3.png',
    'Q15a': f'{prefix}_15_图1.png',
    'Q15b': f'{prefix}_15_图2.png',
}

all_specs = []

for pg, label, caption_kw in figures:
    png_path = f'_pdf_pages/hq_p{pg:02d}.png'
    print(f'\n{"="*60}')
    print(f'{label} (Page {pg}, "{caption_kw}")')

    page_items = ocr_page(png_path)
    page_w, page_h = Image.open(png_path).size

    # Prefer standalone figure labels. Also handle OCR errors:
    # "I5"→"15", "6"→"b", "笫"→"第"
    def is_fig_label(t):
        t_clean = t.replace('I', '1').replace('l', '1').replace('笫', '第')
        return bool(re.match(r'^图\s*[a-zA-Z]\s*$', t) or
                   re.search(r'^[第笫]\s*[\dI]+[\d]*\s*题\s*图\s*[a-zA-Z0-9]?$', t_clean))

    captions = [(t, x0, y0, x1, y1, c) for t, x0, y0, x1, y1, c in page_items if is_fig_label(t)]
    if not captions:
        captions = [(t, x0, y0, x1, y1, c) for t, x0, y0, x1, y1, c in page_items
                    if caption_kw in t or caption_kw.replace('15', 'I5').replace('b', '6') in t]
    if not captions:
        print(f'  SKIP: no caption found')
        continue

    cap = captions[0]
    if len(captions) > 1 and label in ('Q14b', 'Q15b'):
        cap = captions[-1]
    # For standalone '图a' or '图b', pick the right one
    if len(captions) > 1:
        if label == 'Q14a':
            cap = [c for c in captions if c[0].strip() == '图a'][0] if [c for c in captions if c[0].strip() == '图a'] else captions[0]
        elif label == 'Q14b':
            cap = [c for c in captions if c[0].strip() == '图b'][0] if [c for c in captions if c[0].strip() == '图b'] else captions[-1]
    print(f'  Caption: "{cap[0]}" pos=({cap[1]},{cap[2]})')

    left, top, right, bot = find_boundary(page_items, cap, page_w, page_h)

    for it in range(5):
        crop = Image.open(png_path).crop((left, top, right, bot))
        tmp = f'_pdf_pages/_tmp_{label}.png'
        crop.save(tmp)
        clean, issues, crop_items = validate_crop(tmp)
        cw, ch = crop.size
        print(f'  it{it+1}: {cw}x{ch} clean={clean} issues={len(issues)}')
        for iss in issues:
            print(f'    ! {iss}')

        if clean:
            break

        for iss in issues:
            if iss[0] == 'question_text':
                new_top = top + iss[2] + 15
                if new_top < bot - 150:
                    top = new_top
                    print(f'    fix: top -> {top}')
                else:
                    print(f'    skip: top adjustment would exceed bot')
            elif iss[0] == 'too_blank':
                if iss[1] == 'top': top = max(30, top - 120)
                elif iss[1] == 'bottom': bot = min(page_h - 30, bot + 120)
                elif iss[1] == 'left': left = max(30, left - 100)
                elif iss[1] == 'right': right = min(page_w - 30, right + 100)
                print(f'    fix: {iss[1]} adjusted')
            elif iss[0] == 'too_blank':
                top, left = max(30, top - 300), max(30, left - 300)
                bot, right = min(page_h - 30, bot + 300), min(page_w - 30, right + 300)
                print(f'    fix: expanded')

    fname = name_map[label]
    out_path = out_dir / fname
    Image.open(png_path).crop((left, top, right, bot)).save(out_path)
    clean, issues, _ = validate_crop(str(out_path))
    status = 'CLEAN' if clean else f'{len(issues)} issues'
    print(f'  -> {fname} ({out_path.stat().st_size // 1024}KB) {status}')

    all_specs.append({
        'label': label, 'source': f'_pdf_pages/hq_p{pg:02d}.png',
        'box': [int(left), int(top), int(right), int(bot)],
        'output': str(out_path), '_status': status, '_iterations': it + 1,
    })

Path('crop_specs/202511-浙东北.json').write_text(
    json.dumps(all_specs, ensure_ascii=False, indent=2), encoding='utf-8')

print(f'\nDone. {sum(1 for s in all_specs if s["_status"]=="CLEAN")}/{len(all_specs)} clean.')

for f in Path('_pdf_pages').glob('_tmp_*'):
    f.unlink()

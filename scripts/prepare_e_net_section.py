#!/usr/bin/env python3
"""Split one e网通 paper and its answer section from the two source compendia."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


# Each marker is (zero-based page index, vertical cut coordinate in PDF points).
# Sections start after the previous paper's remaining lines on shared pages.
PAPER_MARKERS = [
    (2, 0.0),
    (9, 100.0),
    (15, 345.0),
    (21, 224.0),
    (28, 330.0),
    (35, 330.0),
    (42, 0.0),  # back cover begins
]

ANSWER_MARKERS = [
    (2, 0.0),
    (5, 438.0),
    (9, 94.0),
    (11, 656.0),
    (14, 280.0),
    (17, 265.0),
    (21, 0.0),  # back cover begins
]


def write_section(
    source_path: Path,
    output_path: Path,
    start: tuple[int, float],
    end: tuple[int, float],
) -> None:
    source = fitz.open(source_path)
    output = fitz.open()
    start_page, start_y = start
    end_page, end_y = end
    last_page = end_page if end_y > 0 else end_page - 1

    for page_index in range(start_page, last_page + 1):
        output.insert_pdf(source, from_page=page_index, to_page=page_index)
        copied = output[-1]
        source_rect = source[page_index].rect
        top = start_y if page_index == start_page else 0.0
        bottom = end_y if page_index == end_page and end_y > 0 else source_rect.height
        if top > 0.0 or bottom < source_rect.height:
            copied.set_cropbox(
                fitz.Rect(source_rect.x0, top, source_rect.x1, bottom)
            )

    output.set_metadata(
        {
            "title": output_path.stem,
            "subject": f"Split from {source_path.name}",
        }
    )
    save_path = output_path.with_suffix(".tmp.pdf")
    output.save(save_path, garbage=4, deflate=True)
    output.close()
    source.close()
    save_path.replace(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section", type=int, choices=range(1, 7))
    parser.add_argument("paper_compendium", type=Path)
    parser.add_argument("answer_compendium", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("试卷"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    prefix = f"202607-暑假-高三-e网通{args.section}"
    paper_output = args.output_dir / f"{prefix}.pdf"
    answer_output = args.output_dir / f"{prefix}-答案.pdf"
    for output_path in (paper_output, answer_output):
        if output_path.exists() and not args.overwrite:
            raise FileExistsError(f"Refusing to overwrite: {output_path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    index = args.section - 1
    write_section(
        args.paper_compendium,
        paper_output,
        PAPER_MARKERS[index],
        PAPER_MARKERS[index + 1],
    )
    write_section(
        args.answer_compendium,
        answer_output,
        ANSWER_MARKERS[index],
        ANSWER_MARKERS[index + 1],
    )
    print(paper_output)
    print(answer_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render selected PDF pages to PNG files for question image cropping."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz


def parse_pages(spec: str | None, total: int) -> list[int]:
    if not spec:
        return list(range(1, total + 1))

    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))

    bad = [page for page in pages if page < 1 or page > total]
    if bad:
        raise ValueError(f"Page(s) outside 1..{total}: {bad}")
    return sorted(pages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input PDF path.")
    parser.add_argument(
        "--pages",
        help="1-based page list or ranges, for example: 1-7,10. Defaults to all pages.",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("_pdf_pages"))
    parser.add_argument("--prefix", default="page", help="Output filename prefix.")
    parser.add_argument("--scale", type=float, default=2.2, help="Render scale.")
    args = parser.parse_args()

    doc = fitz.open(args.pdf)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    matrix = fitz.Matrix(args.scale, args.scale)

    for page_number in parse_pages(args.pages, len(doc)):
        page = doc[page_number - 1]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        output = args.out_dir / f"{args.prefix}_p{page_number:02d}.png"
        pix.save(output)
        print(f"{page_number}: {output} ({pix.width}x{pix.height})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

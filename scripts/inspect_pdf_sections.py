#!/usr/bin/env python3
"""Inspect PDF page text to identify section boundaries before splitting."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import fitz


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--preview-lines", type=int, default=12)
    parser.add_argument(
        "--find",
        action="append",
        default=[],
        help="Also print matching text spans and their page coordinates.",
    )
    args = parser.parse_args()

    for path in args.pdfs:
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        document = fitz.open(path)
        print(f"\n## {path}")
        print(f"sha256={digest} pages={len(document)} bytes={path.stat().st_size}")
        for page_number, page in enumerate(document, start=1):
            lines = [
                " ".join(line.split())
                for line in page.get_text("text").splitlines()
                if line.strip()
            ]
            preview = " | ".join(lines[: args.preview_lines])
            print(
                f"p{page_number:03d} chars={len(page.get_text('text')):5d} "
                f"images={len(page.get_images(full=True)):2d} :: {preview}"
            )
            if args.find:
                page_dict = page.get_text("dict")
                for block in page_dict["blocks"]:
                    for line in block.get("lines", []):
                        line_text = "".join(
                            span.get("text", "") for span in line.get("spans", [])
                        ).strip()
                        if any(pattern in line_text for pattern in args.find):
                            x0, y0, x1, y1 = line["bbox"]
                            print(
                                "  MATCH "
                                f"bbox=({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) "
                                f"text={line_text}"
                            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Crop question-local images from rendered page PNG files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


def load_spec(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Crop spec must be a JSON list.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="JSON crop spec.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Base directory for relative source/output paths.",
    )
    args = parser.parse_args()

    count = 0
    for item in load_spec(args.spec):
        source = args.base_dir / item["source"]
        output = args.base_dir / item["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        image = Image.open(source)
        box_value = item.get("box")
        if box_value is None:
            image.save(output)
            box = None
        else:
            box = tuple(box_value)
            if len(box) != 4:
                raise ValueError(f"Invalid box for {output}: {box}")
            image.crop(box).save(output)
        count += 1
        label = item.get("label", output.name)
        print(f"{label}: {source} {box} -> {output}")

    print(f"cropped {count} image(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

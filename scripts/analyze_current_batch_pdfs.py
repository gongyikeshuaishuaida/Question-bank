from __future__ import annotations

import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]

PREFIXES = [
    "202604-温州-高三-二模",
    "202605-上虞-高三-月考",
    "202605-义乌柯桥-高三-月考",
    "202605-卓越联盟-高三-月考",
    "202605-县域教研-高三-月考",
    "202605-县域联盟-高二-学考",
    "202605-强基联盟-高三-月考",
    "202605-诸暨-高三-三模",
]

Q_RE = re.compile(r"^\s*([1-9]|1[0-5])\s*[\.。．、]")


def main() -> None:
    for prefix in PREFIXES:
        pdf = ROOT / "试卷" / f"{prefix}.pdf"
        doc = fitz.open(pdf)
        print(f"\n## {prefix}: {len(doc)} page(s)")
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            starts: list[str] = []
            for line in text.splitlines():
                line = line.strip()
                m = Q_RE.match(line)
                if m and len(starts) < 12:
                    starts.append(line[:40])
            print(f"p{i:02d}: chars={len(text):5d} starts={starts}")


if __name__ == "__main__":
    main()

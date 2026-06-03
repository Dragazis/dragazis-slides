#!/usr/bin/env python3
"""Build index.json for the dragazis-slides repo.

Reads every ig_XXXX carousel under slides/, OCRs each slide (Greek+English
via tesseract), cleans the page markers and footer signature, and writes a
searchable index.json at the repo root.

Run from the repo root:  python3 build_index.py
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SLIDES_DIR = ROOT / "slides"
OUT = ROOT / "index.json"

# Slide files in carousel order, with a role label for each.
SLIDE_ORDER = [
    ("slide_1_hook.png", "hook"),
    ("slide_2_context.png", "context"),
    ("slide_3_insight.png", "insight"),
    ("slide_4_practical.png", "practical"),
    ("slide_5_cta.png", "cta"),
]

# Lines to strip: page markers like "2/5" and the author footer.
PAGE_MARKER = re.compile(r"^\s*\d\s*[/\\]\s*\d\s*$")
FOOTER = re.compile(r"Δραγάζης|dragazis\.gr", re.IGNORECASE)


def ocr(path: Path) -> str:
    """OCR a single image and return cleaned text (one space-joined block)."""
    result = subprocess.run(
        ["tesseract", str(path), "-", "-l", "ell+eng", "--psm", "6"],
        capture_output=True,
        text=True,
    )
    lines = []
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line or PAGE_MARKER.match(line) or FOOTER.search(line):
            continue
        lines.append(line)
    return " ".join(lines).strip()


def build():
    entries = []
    dirs = sorted(d for d in SLIDES_DIR.iterdir() if d.is_dir())
    for d in dirs:
        slides = {}
        for fname, role in SLIDE_ORDER:
            fpath = d / fname
            slides[role] = ocr(fpath) if fpath.exists() else ""
        entries.append(
            {
                "id": d.name,
                "path": f"slides/{d.name}",
                "hook": slides.get("hook", ""),
                "text": " ".join(slides[r] for _, r in SLIDE_ORDER if slides.get(r)),
                "slides": slides,
            }
        )
        print(f"  {d.name}: {slides.get('hook', '')[:60]}")
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(entries)} carousels to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    build()

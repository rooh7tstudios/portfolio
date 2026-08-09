#!/usr/bin/env python3
"""
build_library.py

Scans /library/ and all subfolders for PDFs and notes (.md / .txt).
Subfolder name becomes the category tag on each card.
Writes library.json to repo root.

Stdlib only, no dependencies.
"""
import json
import re
from pathlib import Path

LIBRARY_DIR = Path("library")
OUTPUT_FILE = Path("library.json")

# Manual overrides for legacy files living directly in library/ (no subfolder yet)
CATEGORY_OVERRIDES = {
    "Richard_Stevens-TCP-IP_Illustrated-EN.pdf": "networking",
    "SEv3.pdf": "cybersecurity",
}
TITLE_OVERRIDES = {
    "Richard_Stevens-TCP-IP_Illustrated-EN.pdf": "TCP/IP Illustrated",
    "SEv3.pdf": "Security Engineering (3rd Edition)",
}


def _titlecase_word(word: str) -> str:
    return word.upper() if len(word) <= 3 else word.capitalize()


def clean_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    stem = re.sub(r"^\d+-", "", stem)
    stem = re.sub(r"[-_]+", " ", stem).strip()
    return " ".join(_titlecase_word(w) for w in stem.split())


def clean_category(folder_name: str) -> str:
    parts = re.sub(r"[-_]+", " ", folder_name).strip().split()
    return " ".join(_titlecase_word(w) for w in parts)


def split_heading(text: str, fallback: str):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            title = line.strip().lstrip("#").strip()
            body = "\n".join(lines[:i] + lines[i + 1:]).strip("\n")
            return title, body
    return fallback, text


def collect_files(directory: Path):
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".pdf", ".md", ".txt"):
            continue
        relative = path.relative_to(directory)
        parts = relative.parts
        if len(parts) > 1:
            category = clean_category(parts[0])
        else:
            override = CATEGORY_OVERRIDES.get(path.name)
            category = clean_category(override) if override else None
        yield path, category


def build():
    items = []

    if not LIBRARY_DIR.exists():
        OUTPUT_FILE.write_text("[]")
        print(f"No {LIBRARY_DIR}/ folder found -- wrote empty library.json")
        return

    for path, category in collect_files(LIBRARY_DIR):
        ext = path.suffix.lower()
        base = {"category": category}

        if ext == ".pdf":
            items.append({
                **base,
                "type": "pdf",
                "title": TITLE_OVERRIDES.get(path.name, clean_title(path.name)),
                "path": "/" + str(path).replace("\\", "/"),
                "size_kb": round(path.stat().st_size / 1024),
            })
        elif ext in (".md", ".txt"):
            text = path.read_text(encoding="utf-8", errors="replace")
            title, body = split_heading(text, clean_title(path.name))
            items.append({
                **base,
                "type": "note",
                "title": title,
                "content": body,
            })

    OUTPUT_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"Wrote {len(items)} item(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    build()

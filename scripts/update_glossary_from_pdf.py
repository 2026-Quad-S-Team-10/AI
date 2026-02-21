# -*- coding: utf-8 -*-
import argparse
import json
import re
from pathlib import Path

import pdfplumber


def clean_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_header_or_footer(line: str) -> bool:
    if not line:
        return True
    if re.fullmatch(r"\d+", line):
        return True
    if "경제금융용어" in line:
        return True
    return False


def parse_aliases_from_line(line: str):
    line = line.replace("연관검색어", "").strip()
    if not line:
        return []
    parts = re.split(r"[·,;]", line)
    return [p.strip() for p in parts if p.strip()]


def extract_lines_from_pdf(pdf_path: Path, start_page: int):
    lines = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages[start_page:]:
            text = page.extract_text() or ""
            for raw in text.splitlines():
                line = clean_line(raw)
                if is_header_or_footer(line):
                    continue
                if line:
                    lines.append(line)
    return lines


def build_definition_alias_map(terms, lines):
    term_set = set(terms)
    term_order = terms
    definitions = {t: "" for t in term_order}
    aliases = {t: [] for t in term_order}

    current_term = None
    current_def = []
    current_alias = []
    in_alias = False

    def flush():
        if current_term is None:
            return
        if current_def:
            definitions[current_term] = " ".join(current_def).strip()
        if current_alias:
            aliases[current_term] = current_alias[:]

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("연관검색어"):
            in_alias = True
            current_alias.extend(parse_aliases_from_line(line))
            i += 1
            continue

        matched_term = None
        if line in term_set:
            matched_term = line
        else:
            if i + 1 < len(lines):
                combined = f"{line} {lines[i + 1]}"
                if combined in term_set:
                    matched_term = combined
                    i += 1  # consume next line

        if matched_term:
            flush()
            current_term = matched_term
            current_def = []
            current_alias = []
            in_alias = False
            i += 1
            continue

        if current_term:
            if in_alias:
                current_alias.append(line)
            else:
                current_def.append(line)

        i += 1

    flush()
    return definitions, aliases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="PDF file path")
    parser.add_argument(
        "--glossary",
        default="storage/glossary.json",
        help="Glossary JSON path (default: storage/glossary.json)",
    )
    parser.add_argument(
        "--body-start",
        type=int,
        required=True,
        help="Body start page (1-based, inclusive)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    glossary_path = Path(args.glossary)

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if not glossary_path.exists():
        raise SystemExit(f"Glossary not found: {glossary_path}")

    glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
    terms = [item["term"] for item in glossary if "term" in item]

    lines = extract_lines_from_pdf(pdf_path, start_page=args.body_start - 1)
    definitions, aliases = build_definition_alias_map(terms, lines)

    updated = []
    for term in terms:
        updated.append(
            {
                "term": term,
                "definition": definitions.get(term, ""),
                "aliases": aliases.get(term, []),
            }
        )

    glossary_path.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Updated {len(updated)} terms in {glossary_path}")


if __name__ == "__main__":
    main()

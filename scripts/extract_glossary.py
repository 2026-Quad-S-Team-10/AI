import argparse
import json
import re
from pathlib import Path

import pdfplumber


def _clean_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def _is_header_or_footer(line: str) -> bool:
    if not line:
        return True
    if re.fullmatch(r"\d+", line):
        return True
    if "경제금융용어" in line:
        return True
    return False


def _split_term_definition(line: str):
    # Common separators: " : ", ":", " - ", "–", "—"
    for sep in [" : ", ": ", ":", " - ", " – ", " — "]:
        if sep in line:
            parts = line.split(sep, 1)
            term = parts[0].strip()
            definition = parts[1].strip()
            if term and definition:
                return term, definition
    # Try multiple spaces as separator
    m = re.match(r"^(.{1,40}?)\s{2,}(.+)$", line)
    if m:
        term = m.group(1).strip()
        definition = m.group(2).strip()
        if term and definition:
            return term, definition
    return None, None


def extract_glossary(pdf_path: Path):
    entries = []
    current_term = None
    current_def = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [
                _clean_line(l)
                for l in text.splitlines()
                if _clean_line(l)
            ]

            for line in lines:
                if _is_header_or_footer(line):
                    continue

                term, definition = _split_term_definition(line)
                if term:
                    if current_term:
                        entries.append(
                            {
                                "term": current_term,
                                "definition": " ".join(current_def).strip(),
                            }
                        )
                    current_term = term
                    current_def = [definition]
                else:
                    if current_term:
                        current_def.append(line)

    if current_term:
        entries.append(
            {
                "term": current_term,
                "definition": " ".join(current_def).strip(),
            }
        )

    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="PDF file path")
    parser.add_argument(
        "-o",
        "--output",
        default="storage/glossary.json",
        help="Output JSON path (default: storage/glossary.json)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    entries = extract_glossary(pdf_path)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Saved {len(entries)} entries to {output_path}")


if __name__ == "__main__":
    main()

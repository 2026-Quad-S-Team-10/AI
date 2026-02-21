import argparse
import json
import os
import re
from pathlib import Path

import pdfplumber


class EconomicTermParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.entries = []

    def _clean_line(self, line):
        line = line.replace("\u00a0", " ")
        line = re.sub(r"\s+", " ", line)
        return line.strip()

    def _is_header_or_footer(self, line):
        if not line:
            return True
        if re.fullmatch(r"\d+", line):
            return True
        if "경제금융용어" in line:
            return True
        return False

    def _split_term_definition(self, line):
        for sep in [" : ", ": ", ":", " - ", " – ", " — "]:
            if sep in line:
                term, definition = line.split(sep, 1)
                term = term.strip()
                definition = definition.strip()
                if term and definition:
                    return term, definition
        match = re.match(r"^(.{1,40}?)\s{2,}(.+)$", line)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if term and definition:
                return term, definition
        return None, None

    def _is_term_line(self, line):
        # Term line: short, no leading spaces, not ending with punctuation
        if not line:
            return False
        if len(line) > 60:
            return False
        if re.search(r"[.!?]$", line):
            return False
        if "연관검색어" in line:
            return False
        return True

    def _join_lines(self, left, right):
        if not left:
            return right
        if left.endswith(("/", "+", "(", "[")):
            return f"{left}{right}"
        return f"{left} {right}"

    def _parse_aliases(self, line):
        # Example: "연관검색어 총부채원리금상환비율(DSR)"
        line = line.replace("연관검색어", "").strip()
        if not line:
            return []
        parts = re.split(r"[·,;]", line)
        return [p.strip() for p in parts if p.strip()]

    def extract_terms(self, start_page=0):
        """
        PDF를 읽어 용어와 설명을 추출합니다.
        """
        print(f"[{self.file_path}] 분석 시작...")

        current_term = None
        current_definition = []
        current_aliases = []

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages[start_page:]:
                text = page.extract_text() or ""
                lines = [
                    self._clean_line(line) for line in text.splitlines()
                ]

                for line in lines:
                    if self._is_header_or_footer(line):
                        continue

                    if line.startswith("연관검색어"):
                        if current_term:
                            current_aliases.extend(self._parse_aliases(line))
                        continue

                    term, definition = self._split_term_definition(line)
                    if term:
                        if current_term and current_definition:
                            self.entries.append(
                                {
                                    "term": current_term,
                                    "definition": " ".join(current_definition).strip(),
                                    "aliases": current_aliases,
                                }
                            )
                        current_term = term
                        current_definition = [definition]
                        current_aliases = []
                    elif self._is_term_line(line):
                        if current_term and current_definition:
                            self.entries.append(
                                {
                                    "term": current_term,
                                    "definition": " ".join(current_definition).strip(),
                                    "aliases": current_aliases,
                                }
                            )
                        current_term = line
                        current_definition = []
                        current_aliases = []
                    else:
                        if current_term:
                            current_definition.append(line)

        if current_term and current_definition:
            self.entries.append(
                {
                    "term": current_term,
                    "definition": " ".join(current_definition).strip(),
                    "aliases": current_aliases,
                }
            )

        print(f"총 {len(self.entries)}개의 용어가 추출되었습니다.")
        return self.entries

    def extract_terms_from_toc(self, toc_start, toc_end):
        toc_terms = []
        buffer_line = ""

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages[toc_start:toc_end + 1]:
                text = page.extract_text() or ""
                lines = [
                    self._clean_line(line) for line in text.splitlines()
                ]
                for line in lines:
                    if self._is_header_or_footer(line):
                        continue

                    # Remove dot leaders and trailing page numbers
                    cleaned = re.sub(r"[·.]+", " ", line)
                    cleaned = re.sub(r"\s+\d+\s*$", "", cleaned).strip()

                    if cleaned:
                        if buffer_line:
                            cleaned = self._join_lines(buffer_line, cleaned)
                            buffer_line = ""
                        toc_terms.append(cleaned)
                        continue

                    # Buffer lines that are likely split term lines
                    if line:
                        buffer_line = self._join_lines(buffer_line, line)

        return toc_terms

    def extract_definitions_by_toc(self, toc_terms, body_start):
        toc_set = set(toc_terms)
        toc_terms_sorted = sorted(toc_terms, key=len, reverse=True)
        definitions = {term: "" for term in toc_terms}

        current_term = None
        current_definition = []

        def flush():
            if current_term is None:
                return
            if current_definition:
                definitions[current_term] = " ".join(current_definition).strip()

        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages[body_start:]:
                text = page.extract_text() or ""
                lines = [
                    self._clean_line(line) for line in text.splitlines()
                ]
                for line in lines:
                    if self._is_header_or_footer(line):
                        continue
                    if not line:
                        continue

                    if line.startswith("연관검색어"):
                        continue

                    matched_term = None
                    if line in toc_set:
                        matched_term = line
                    else:
                        for term in toc_terms_sorted:
                            if line == term:
                                matched_term = term
                                break

                    if matched_term:
                        flush()
                        current_term = matched_term
                        current_definition = []
                        continue

                    if current_term:
                        current_definition.append(line)

        flush()

        self.entries = [
            {"term": term, "definition": definitions.get(term, "")}
            for term in toc_terms
        ]
        return self.entries

    def save_to_json(self, output_path):
        """
        결과를 JSON 파일로 저장합니다.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="PDF file path")
    parser.add_argument(
        "--out",
        default="storage/glossary.json",
        help="Output JSON path (default: storage/glossary.json)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="Start page index (0-based). Legacy mode only.",
    )
    parser.add_argument(
        "--toc-start",
        type=int,
        help="TOC start page (1-based, inclusive)",
    )
    parser.add_argument(
        "--toc-end",
        type=int,
        help="TOC end page (1-based, inclusive)",
    )
    parser.add_argument(
        "--body-start",
        type=int,
        help="Body start page (1-based, inclusive)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    parser_obj = EconomicTermParser(str(pdf_path))
    if args.toc_start and args.toc_end and args.body_start:
        toc_start = args.toc_start - 1
        toc_end = args.toc_end - 1
        body_start = args.body_start - 1
        toc_terms = parser_obj.extract_terms_from_toc(toc_start, toc_end)
        parser_obj.extract_definitions_by_toc(toc_terms, body_start)
    else:
        parser_obj.extract_terms(start_page=args.start_page)
    parser_obj.save_to_json(args.out)


if __name__ == "__main__":
    main()

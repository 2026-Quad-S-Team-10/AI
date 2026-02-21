import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collector.news_api import NewsCollector
from processor.analyzer import EconomicNewsProcessor


def load_glossary_entries(glossary_path):
    path = Path(glossary_path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [
            {"term": term, "definition": definition, "aliases": []}
            for term, definition in data.items()
        ]
    if not isinstance(data, list):
        return []

    entries = []
    for item in data:
        term = (item.get("term") or "").strip()
        if not term:
            continue
        entries.append(
            {
                "term": term,
                "definition": (item.get("definition") or "").strip(),
                "aliases": [a.strip() for a in (item.get("aliases") or []) if a.strip()],
            }
        )
    return entries


def pick_daily_entry(entries, date_value=None):
    if not entries:
        return None, None
    date_value = date_value or dt.date.today().isoformat()
    seed = int(date_value.replace("-", ""))
    ordered = sorted(entries, key=lambda item: item["term"])
    return ordered[seed % len(ordered)], date_value


def _unique_keywords(entry):
    seen = set()
    keywords = []
    for value in [entry["term"]] + entry.get("aliases", []):
        if value and value not in seen:
            seen.add(value)
            keywords.append(value)
    return keywords


def _merge_articles(keyword_to_articles):
    merged = {}
    for keyword, articles in keyword_to_articles.items():
        for article in articles:
            key = article.get("url") or article.get("title")
            if not key:
                continue
            if key not in merged:
                merged[key] = {
                    **article,
                    "matched_keywords": [keyword],
                }
            else:
                merged[key]["matched_keywords"].append(keyword)
    return list(merged.values())


def build_cloze_for_entry(summary, entry):
    if not summary:
        return {"question": "", "answer": ""}
    for keyword in _unique_keywords(entry):
        if keyword in summary:
            return {"question": summary.replace(keyword, "____", 1), "answer": keyword}
    return {"question": summary, "answer": ""}


def build_ox_for_entry(entry, fallback_entry=None):
    quizzes = []
    term = entry.get("term", "")
    definition = (entry.get("definition") or "").strip()
    if term and definition:
        quizzes.append(
            {
                "question": f"{term}은(는) {definition}을(를) 의미한다.",
                "answer": True,
            }
        )
    if fallback_entry:
        other_def = (fallback_entry.get("definition") or "").strip()
        if term and other_def and other_def != definition:
            quizzes.append(
                {
                    "question": f"{term}은(는) {other_def}을(를) 의미한다.",
                    "answer": False,
                }
            )
    return quizzes


def main():
    glossary_path = "storage/glossary.json"
    entries = load_glossary_entries(glossary_path)
    entry, date_value = pick_daily_entry(entries)
    if not entry:
        print("glossary.json에서 용어를 찾지 못했습니다.")
        return

    collector = NewsCollector()
    keywords = _unique_keywords(entry)

    keyword_to_articles = {}
    for keyword in keywords:
        keyword_to_articles[keyword] = collector.fetch_economic_news(
            query=keyword, page_size=10, sort="date"
        )

    articles = _merge_articles(keyword_to_articles)

    processor = EconomicNewsProcessor(glossary_path=glossary_path)
    fallback_entry = None
    if len(entries) > 1:
        ordered = sorted(entries, key=lambda item: item["term"])
        idx = ordered.index(entry)
        fallback_entry = ordered[(idx + 1) % len(ordered)]

    processed_articles = []
    for article in articles:
        summary = processor.build_summary(article)
        cloze = build_cloze_for_entry(summary, entry)
        ox = build_ox_for_entry(entry, fallback_entry=fallback_entry)
        processed_articles.append(
            {
                "article": article,
                "summary": summary,
                "quiz": {"cloze": cloze, "ox": ox},
                "categories": processor.classify(article),
                "matched_keywords": article.get("matched_keywords", []),
            }
        )

    output = {
        "date": date_value,
        "term": entry,
        "keywords": keywords,
        "articles": processed_articles,
    }

    output_path = Path("storage/daily_topic.json")
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved daily topic to {output_path}")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

from collector.news_api import NewsCollector
from processor.analyzer import EconomicNewsProcessor


def main():
    collector = NewsCollector()
    articles = collector.fetch_economic_news(query="경제", page_size=5, sort="date")

    processor = EconomicNewsProcessor(glossary_path="storage/glossary.json")
    results = [processor.process_article(article) for article in articles]

    output_path = Path("storage/processed_news.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved {len(results)} results to {output_path}")


if __name__ == "__main__":
    main()

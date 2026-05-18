from typing import Any

import pandas as pd

try:
    from app.services.news_csv_service import get_valid_news_dataframe
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from news_csv_service import get_valid_news_dataframe


NEWS_ITEM_COLUMNS = (
    "title",
    "content",
    "url",
    "source",
    "category",
    "pubDate",
    "summary",
    "term",
)


def filter_news_by_term(term: str, category: str | None = None) -> pd.DataFrame:
    """Return news rows matching the given term and optional category."""
    search_term = term.strip()
    if not search_term:
        raise ValueError("term must not be empty.")

    df = get_valid_news_dataframe()

    term_series = df["term"].astype(str).str.strip()
    filtered_df = df[term_series == search_term].copy()

    if category is not None:
        search_category = category.strip()
        if search_category:
            category_series = filtered_df["category"].astype(str).str.strip()
            filtered_df = filtered_df[category_series == search_category].copy()

    filtered_df = _sort_by_latest_pub_date(filtered_df)

    if filtered_df.empty:
        message = f"No news found for term: {search_term}"
        if category is not None and category.strip():
            message += f", category: {category.strip()}"
        raise ValueError(message)

    return filtered_df.reset_index(drop=True)


def get_latest_news_by_term(term: str, category: str | None = None) -> dict[str, Any]:
    """Return the latest representative news item for a term."""
    filtered_df = filter_news_by_term(term, category)

    if filtered_df.empty:
        raise ValueError(f"No valid news found for term: {term.strip()}")

    return format_news_item(filtered_df.iloc[0])


def format_news_item(row: pd.Series) -> dict[str, Any]:
    """Convert a news DataFrame row to a dict for downstream services."""
    return {column: _normalize_value(row.get(column)) for column in NEWS_ITEM_COLUMNS}


def _sort_by_latest_pub_date(df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = df.copy()
    sorted_df["_pubDateParsed"] = pd.to_datetime(
        sorted_df["pubDate"],
        errors="coerce",
        utc=True,
    )

    return sorted_df.sort_values(
        by="_pubDateParsed",
        ascending=False,
        na_position="last",
    ).drop(columns=["_pubDateParsed"])


def _normalize_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def print_latest_news_lookup_summary(
    term: str,
    category: str | None = None,
) -> None:
    """Simple smoke-test helper for local term-based news lookup checks."""
    news_item = get_latest_news_by_term(term, category)
    print(
        "Latest news: "
        f"[{news_item['term']}/{news_item['category']}] "
        f"{news_item['title']}"
    )


if __name__ == "__main__":
    print_latest_news_lookup_summary("수요")

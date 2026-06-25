from pathlib import Path

import pandas as pd


NEWS_CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "news.csv"

REQUIRED_NEWS_COLUMNS = (
    "term",
    "category",
    "title",
    "summary",
    "content",
    "source",
    "url",
    "pubDate",
)


def load_news_csv(csv_path: str | Path = NEWS_CSV_PATH) -> pd.DataFrame:
    """Load the news CSV file into a pandas DataFrame."""
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"News CSV file was not found at {path}. "
            "Place the CSV file at app/data/news.csv."
        )

    return pd.read_csv(path)


def validate_news_columns(df: pd.DataFrame) -> None:
    """Validate that all required news CSV columns exist."""
    missing_columns = [
        column for column in REQUIRED_NEWS_COLUMNS if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "News CSV is missing required columns: "
            f"{', '.join(missing_columns)}"
        )


def get_valid_news_dataframe(csv_path: str | Path = NEWS_CSV_PATH) -> pd.DataFrame:
    """Return a validated DataFrame with rows missing content removed."""
    df = load_news_csv(csv_path)
    validate_news_columns(df)

    valid_df = df.dropna(subset=["content"]).copy()
    valid_df["content"] = valid_df["content"].astype(str).str.strip()
    valid_df = valid_df[valid_df["content"] != ""]

    return valid_df.reset_index(drop=True)


def print_news_csv_load_summary(csv_path: str | Path = NEWS_CSV_PATH) -> None:
    """Simple smoke-test helper for local CSV loading checks."""
    df = get_valid_news_dataframe(csv_path)
    print(f"Loaded {len(df)} valid news rows from {Path(csv_path)}")


if __name__ == "__main__":
    print_news_csv_load_summary()

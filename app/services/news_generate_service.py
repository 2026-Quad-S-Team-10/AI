from typing import Any

try:
    from app.services.keyword_explanation_service import generate_keyword_explanation
    from app.services.news_preprocess_service import clean_news_content
    from app.services.news_query_service import get_latest_news_by_term
    from app.services.news_quiz_service import generate_news_quiz
    from app.services.news_summary_service import generate_news_summary
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from keyword_explanation_service import generate_keyword_explanation
    from news_preprocess_service import clean_news_content
    from news_query_service import get_latest_news_by_term
    from news_quiz_service import generate_news_quiz
    from news_summary_service import generate_news_summary


def generate_news_learning_content(
    term: str,
    difficulty: str = "BEGINNER",
    category: str | None = None,
) -> dict[str, Any]:
    """Generate summary, keyword explanation, and quiz for a representative news item."""
    if term is None or not str(term).strip():
        raise ValueError("term must not be empty.")

    news_item = get_latest_news_by_term(term.strip(), category)
    content = news_item.get("content")
    if content is None or not str(content).strip():
        raise ValueError("news content must not be empty.")

    cleaned_content = clean_news_content(str(content))
    title = str(news_item.get("title") or "").strip()
    if not title:
        raise ValueError("news title must not be empty.")

    news_term = str(news_item.get("term") or term).strip()

    summary = generate_news_summary(news_term, title, cleaned_content)
    keyword_explanation = generate_keyword_explanation(
        news_term,
        title,
        cleaned_content,
    )
    quiz = generate_news_quiz(
        news_term,
        title,
        cleaned_content,
        difficulty,
    )

    return {
        "term": news_term,
        "category": news_item.get("category"),
        "newsTitle": title,
        "newsSummary": news_item.get("summary"),
        "newsUrl": news_item.get("url"),
        "source": news_item.get("source"),
        "pubDate": news_item.get("pubDate"),
        "summary": summary,
        "keywordExplanation": keyword_explanation,
        "quiz": quiz,
    }

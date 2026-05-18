from fastapi.testclient import TestClient

from app.main import app
from app.routers import news_generate_router


client = TestClient(app)


def test_generate_news_success(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        return {
            "term": term,
            "category": category,
            "newsTitle": "뉴스 제목",
            "newsSummary": "CSV 기존 요약",
            "newsUrl": "https://example.com/news",
            "source": "example.com",
            "pubDate": "Sun, 12 Apr 2026 13:18:00 +0900",
            "summary": [
                "첫 번째 요약 문장입니다.",
                "두 번째 요약 문장입니다.",
                "세 번째 요약 문장입니다.",
            ],
            "keywordExplanation": "수요는 필요한 정도를 뜻합니다.",
            "quiz": [
                {
                    "type": "OX",
                    "question": "수요는 필요한 정도를 뜻한다.",
                    "answer": "O",
                    "explanation": "수요는 필요와 구매 의사를 뜻합니다.",
                },
                {
                    "type": "MULTIPLE_CHOICE",
                    "question": "기사에서 수요와 가장 관련 있는 내용은?",
                    "options": ["자금 지원", "세금 폐지", "수출 중단", "소비 감소"],
                    "answer": "자금 지원",
                    "explanation": "기사에서는 자금 지원을 설명합니다.",
                },
            ],
        }

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "BEGINNER"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["term"] == "수요"
    assert body["newsTitle"] == "뉴스 제목"
    assert body["newsUrl"] == "https://example.com/news"
    assert len(body["summary"]) == 3
    assert body["keywordExplanation"]
    assert len(body["quiz"]) == 2
    for quiz_item in body["quiz"]:
        assert quiz_item["question"]
        assert quiz_item["answer"]
        assert quiz_item["explanation"]


def test_generate_news_success_with_category(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        return {
            "term": term,
            "category": category,
            "newsTitle": "국내 뉴스 제목",
            "newsSummary": "CSV 기존 요약",
            "newsUrl": "https://example.com/domestic-news",
            "source": "example.com",
            "pubDate": "Sun, 12 Apr 2026 13:18:00 +0900",
            "summary": ["요약 1", "요약 2", "요약 3"],
            "keywordExplanation": "쉬운 용어 설명",
            "quiz": [
                {
                    "type": "OX",
                    "question": "문제",
                    "answer": "O",
                    "explanation": "해설",
                }
            ],
        }

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "BEGINNER", "category": "국내"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "국내"


def test_generate_news_not_found(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        raise ValueError(f"No news found for term: {term}")

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "없는용어", "difficulty": "BEGINNER"},
    )

    assert response.status_code == 404
    assert "No news found for term: 없는용어" in response.json()["detail"]


def test_generate_news_empty_content(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        raise ValueError("news content must not be empty.")

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "BEGINNER"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "news content must not be empty."


def test_generate_news_invalid_difficulty():
    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "EASY"},
    )

    assert response.status_code == 422


def test_generate_news_openai_failure(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        raise RuntimeError("OpenAI API call failed: invalid API key")

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "BEGINNER"},
    )

    assert response.status_code == 500
    assert "OpenAI API call failed" in response.json()["detail"]


def test_generate_news_gpt_parse_failure(monkeypatch):
    def fake_generate_news_learning_content(
        term: str,
        difficulty: str = "BEGINNER",
        category: str | None = None,
    ) -> dict:
        raise ValueError("Failed to parse quiz response as JSON: invalid JSON")

    monkeypatch.setattr(
        news_generate_router,
        "generate_news_learning_content",
        fake_generate_news_learning_content,
    )

    response = client.post(
        "/ai/news/generate",
        json={"term": "수요", "difficulty": "BEGINNER"},
    )

    assert response.status_code == 500
    assert "Failed to parse quiz response as JSON" in response.json()["detail"]

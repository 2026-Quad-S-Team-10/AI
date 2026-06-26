from fastapi.testclient import TestClient

from app.main import app
from app.routers import news_generate_router
from app.services import news_summary_service
from app.services.news_quiz_service import parse_quiz_response
from app.services.news_summary_service import parse_summary_response


client = TestClient(app)


def test_parse_summary_response_rejects_ellipsis_ending():
    response_text = """
    {
      "summary": [
        "은행은 중소기업 자금 부담을 줄이기 위한 프로그램을 운영합니다.",
        "이 지원은 정책자금 이용 기업에 금리 우대 혜택을 제공한다는 내용입니다.",
        "지역별 수요 편차와 접근성 문제가 변수로..."
      ]
    }
    """

    try:
        parse_summary_response(response_text)
    except ValueError as exc:
        assert "must not end with an ellipsis" in str(exc)
    else:
        raise AssertionError("Expected ellipsis-ended summary to be rejected.")


def test_generate_news_summary_uses_larger_token_limit_and_retries(monkeypatch):
    responses = iter(
        [
            """
            {
              "summary": [
                "은행은 중소기업 자금 부담을 줄이기 위한 프로그램을 운영합니다.",
                "이 지원은 정책자금 이용 기업에 금리 우대 혜택을 제공한다는 내용입니다.",
                "지역별 수요 편차와 접근성 문제가 변수로..."
              ]
            }
            """,
            """
            {
              "summary": [
                "은행은 중소기업 자금 부담을 줄이기 위한 프로그램을 운영합니다.",
                "이 지원은 정책자금 이용 기업에 금리 우대 혜택을 제공한다는 내용입니다.",
                "지역별 수요 편차와 접근성 문제는 실제 지원 효과를 좌우할 수 있습니다."
              ]
            }
            """,
        ]
    )
    calls = []

    def fake_call_openai_chat(prompt: str, max_output_tokens: int | None = None) -> str:
        calls.append((prompt, max_output_tokens))
        return next(responses)

    monkeypatch.setattr(
        news_summary_service,
        "call_openai_chat",
        fake_call_openai_chat,
    )

    summary = news_summary_service.generate_news_summary(
        "수요",
        "뉴스 제목",
        "중소기업의 자금 수요가 늘고 있습니다. 은행은 금리 우대를 제공합니다.",
    )

    assert len(summary) == 3
    assert not summary[-1].endswith("...")
    assert len(calls) == 2
    assert {max_output_tokens for _, max_output_tokens in calls} == {
        news_summary_service.SUMMARY_MAX_OUTPUT_TOKENS
    }


def test_parse_quiz_response_allows_exactly_three_ox_items():
    response_text = """
    {
      "quiz": [
        {
          "type": "OX",
          "question": "수요는 필요와 구매 의사를 뜻한다.",
          "answer": "O",
          "explanation": "수요는 필요와 구매 의사를 포함합니다."
        },
        {
          "type": "OX",
          "question": "뉴스 내용과 경제 용어는 연결될 수 있다.",
          "answer": "O",
          "explanation": "기사 속 상황을 경제 용어로 설명할 수 있습니다."
        },
        {
          "type": "OX",
          "question": "본문에 없는 내용을 정답 근거로 삼아도 된다.",
          "answer": "X",
          "explanation": "정답 근거는 뉴스 본문에 있어야 합니다."
        }
      ]
    }
    """

    quiz = parse_quiz_response(response_text)

    assert len(quiz) == 3
    assert {item["type"] for item in quiz} == {"OX"}


def test_parse_quiz_response_rejects_non_ox_items():
    response_text = """
    {
      "quiz": [
        {
          "type": "OX",
          "question": "문제 1",
          "answer": "O",
          "explanation": "해설 1"
        },
        {
          "type": "MULTIPLE_CHOICE",
          "question": "문제 2",
          "options": ["보기 1", "보기 2", "보기 3", "보기 4"],
          "answer": "보기 1",
          "explanation": "해설 2"
        },
        {
          "type": "OX",
          "question": "문제 3",
          "answer": "X",
          "explanation": "해설 3"
        }
      ]
    }
    """

    try:
        parse_quiz_response(response_text)
    except ValueError as exc:
        assert "must be OX type" in str(exc)
    else:
        raise AssertionError("Expected non-OX quiz item to be rejected.")


def test_parse_quiz_response_rejects_wrong_quiz_count():
    response_text = """
    {
      "quiz": [
        {
          "type": "OX",
          "question": "문제 1",
          "answer": "O",
          "explanation": "해설 1"
        }
      ]
    }
    """

    try:
        parse_quiz_response(response_text)
    except ValueError as exc:
        assert "exactly 3 OX items" in str(exc)
    else:
        raise AssertionError("Expected wrong quiz count to be rejected.")


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
                    "type": "OX",
                    "question": "기사에서는 자금 지원과 관련된 내용을 설명한다.",
                    "answer": "O",
                    "explanation": "기사에서는 자금 지원을 설명합니다.",
                },
                {
                    "type": "OX",
                    "question": "수요는 기사 내용과 전혀 연결되지 않는다.",
                    "answer": "X",
                    "explanation": "수요는 기사 속 자금 필요와 연결됩니다.",
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
    assert len(body["quiz"]) == 3
    for quiz_item in body["quiz"]:
        assert quiz_item["type"] == "OX"
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

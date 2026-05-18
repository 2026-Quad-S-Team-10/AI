from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


Difficulty = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]


class NewsGenerateRequest(BaseModel):
    term: str = Field(
        ...,
        description="조회할 경제 용어",
        examples=["수요"],
    )
    difficulty: Difficulty = Field(
        default="BEGINNER",
        description="퀴즈 난이도",
        examples=["BEGINNER"],
    )
    category: str | None = Field(
        default=None,
        description="선택 뉴스 카테고리 필터",
        examples=["국내"],
    )

    @field_validator("term")
    @classmethod
    def validate_term(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("term must not be empty.")

        return value.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None


class NewsGenerateResponse(BaseModel):
    term: str = Field(..., description="경제 용어")
    category: str | None = Field(default=None, description="뉴스 카테고리")
    newsTitle: str = Field(..., description="대표 뉴스 제목")
    newsSummary: str | None = Field(default=None, description="CSV에 저장된 기존 요약")
    newsUrl: str | None = Field(default=None, description="뉴스 원문 URL")
    source: str | None = Field(default=None, description="뉴스 출처")
    pubDate: str | None = Field(default=None, description="뉴스 발행일")
    summary: list[str] = Field(..., description="GPT가 생성한 3줄 요약")
    keywordExplanation: str = Field(..., description="경제 용어 설명")
    quiz: list[dict[str, Any]] = Field(..., description="학습용 퀴즈 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "term": "수요",
                "category": "국내",
                "newsTitle": "뉴스 제목",
                "newsSummary": "CSV에 있던 기존 요약",
                "newsUrl": "https://example.com/news",
                "source": "예시뉴스",
                "pubDate": "Sun, 12 Apr 2026 13:18:00 +0900",
                "summary": [
                    "첫 번째 요약 문장",
                    "두 번째 요약 문장",
                    "세 번째 요약 문장",
                ],
                "keywordExplanation": "경제 용어가 뉴스에서 어떻게 쓰였는지 쉬운 설명",
                "quiz": [
                    {
                        "type": "OX",
                        "question": "수요는 사람들이 상품이나 서비스를 사고자 하는 욕구를 의미한다.",
                        "answer": "O",
                        "explanation": "수요는 구매하고자 하는 의사와 필요를 뜻합니다.",
                    }
                ],
            }
        }
    }

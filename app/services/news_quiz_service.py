import json
import re
from typing import Any

try:
    from app.services.news_preprocess_service import clean_news_content
    from app.services.openai_service import call_openai_chat
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from news_preprocess_service import clean_news_content
    from openai_service import call_openai_chat


DEFAULT_DIFFICULTY = "BEGINNER"
VALID_DIFFICULTIES = ("BEGINNER", "INTERMEDIATE", "ADVANCED")
QUIZ_FIELD = "quiz"
OX_TYPE = "OX"
REQUIRED_QUIZ_FIELDS = ("type", "question", "answer", "explanation")
REQUIRED_QUIZ_COUNT = 3

DIFFICULTY_GUIDE = {
    "BEGINNER": "용어 뜻과 기사 핵심을 쉽게 묻는다.",
    "INTERMEDIATE": "기사 속 원인과 결과 관계를 묻는다.",
    "ADVANCED": "경제 용어가 실제 경제 상황에 적용되는 방식을 묻는다.",
}


def generate_news_quiz(
    term: str,
    title: str,
    content: str,
    difficulty: str = DEFAULT_DIFFICULTY,
) -> list[dict[str, Any]]:
    """Generate OX quizzes from news content."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")

    cleaned_content = clean_news_content(content)
    normalized_difficulty = _normalize_difficulty(difficulty)
    prompt = build_quiz_prompt(
        term,
        title,
        cleaned_content,
        normalized_difficulty,
    )
    response_text = call_openai_chat(prompt)

    return parse_quiz_response(response_text)


def build_quiz_prompt(
    term: str,
    title: str,
    content: str,
    difficulty: str,
) -> str:
    """Build a prompt for JSON-only news quiz generation."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")
    normalized_difficulty = _normalize_difficulty(difficulty)

    return f"""
너는 경제 초급자를 위한 뉴스 학습 퀴즈 출제자다.
아래 뉴스 제목과 본문만 바탕으로 학습용 퀴즈를 만들어라.

조건:
- 경제 용어와 뉴스 내용이 연결되도록 문제를 만든다.
- 뉴스 본문에 없는 내용을 정답 근거로 만들지 않는다.
- 과장된 표현을 쓰지 않는다.
- 반드시 JSON만 반환한다.
- 최상위 필드는 quiz 하나만 둔다.
- quiz 배열에는 OX 문제만 정확히 3개 포함한다.
- 각 문제에는 type, question, answer, explanation을 포함한다.
- OX 문제의 answer는 반드시 "O" 또는 "X" 중 하나다.
- 해설은 경제 초급자도 이해할 수 있도록 쉽게 작성한다.
- 마크다운 코드블록, 설명 문장, 번호 목록은 쓰지 않는다.

난이도:
{normalized_difficulty} - {DIFFICULTY_GUIDE[normalized_difficulty]}

반환 형식:
{{
  "quiz": [
    {{
      "type": "OX",
      "question": "첫 번째 O/X 문제 문장",
      "answer": "O",
      "explanation": "쉬운 해설"
    }},
    {{
      "type": "OX",
      "question": "두 번째 O/X 문제 문장",
      "answer": "X",
      "explanation": "쉬운 해설"
    }},
    {{
      "type": "OX",
      "question": "세 번째 O/X 문제 문장",
      "answer": "O",
      "explanation": "쉬운 해설"
    }}
  ]
}}

경제 용어:
{term.strip()}

뉴스 제목:
{title.strip()}

뉴스 본문:
{content.strip()}
""".strip()


def parse_quiz_response(response_text: str) -> list[dict[str, Any]]:
    """Parse and validate a JSON quiz response from GPT."""
    _validate_required_text(response_text, "response_text")

    try:
        parsed_response = json.loads(_extract_json_text(response_text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse quiz response as JSON: {exc}") from exc

    if not isinstance(parsed_response, dict):
        raise ValueError("quiz response JSON must be an object.")

    quiz = parsed_response.get(QUIZ_FIELD)
    if not isinstance(quiz, list):
        raise ValueError("quiz response must include a quiz array.")

    if not quiz:
        raise ValueError("quiz array must not be empty.")

    return validate_quiz_items(quiz)


def validate_quiz_items(quiz: list[dict]) -> list[dict[str, Any]]:
    """Validate and normalize quiz items for downstream use."""
    if not isinstance(quiz, list):
        raise ValueError("quiz must be a list.")

    if len(quiz) != REQUIRED_QUIZ_COUNT:
        raise ValueError(
            f"quiz must include exactly {REQUIRED_QUIZ_COUNT} OX items."
        )

    validated_quiz = []

    for index, item in enumerate(quiz, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"quiz item {index} must be an object.")

        normalized_item = _validate_common_quiz_fields(item, index)
        quiz_type = normalized_item["type"]

        if quiz_type == OX_TYPE:
            _validate_ox_quiz_item(normalized_item, index)
        else:
            raise ValueError(f"quiz item {index} must be OX type.")

        validated_quiz.append(normalized_item)

    return validated_quiz


def _validate_common_quiz_fields(
    item: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    normalized_item = dict(item)

    for field in REQUIRED_QUIZ_FIELDS:
        value = normalized_item.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"quiz item {index} must include a non-empty {field} string."
            )
        normalized_item[field] = value.strip()

    normalized_item["type"] = normalized_item["type"].strip().upper()

    return normalized_item


def _validate_ox_quiz_item(item: dict[str, Any], index: int) -> None:
    if item["answer"] not in {"O", "X"}:
        raise ValueError(f"OX quiz item {index} answer must be O or X.")


def _normalize_difficulty(difficulty: str) -> str:
    if difficulty is None:
        return DEFAULT_DIFFICULTY

    normalized_difficulty = str(difficulty).strip().upper()
    if normalized_difficulty not in VALID_DIFFICULTIES:
        return DEFAULT_DIFFICULTY

    return normalized_difficulty


def _extract_json_text(response_text: str) -> str:
    cleaned_text = response_text.strip()
    code_block_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        cleaned_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if code_block_match:
        return code_block_match.group(1).strip()

    start_index = cleaned_text.find("{")
    end_index = cleaned_text.rfind("}")
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError("quiz response did not include a JSON object.")

    return cleaned_text[start_index : end_index + 1]


def _validate_required_text(value: str, field_name: str) -> None:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} must not be empty.")


def print_quiz_parse_sample() -> None:
    """Simple smoke-test helper for local quiz response parsing checks."""
    response_text = json.dumps(
        {
            "quiz": [
                {
                    "type": "OX",
                    "question": "수요는 사람들이 상품이나 서비스를 필요로 하는 정도를 뜻한다.",
                    "answer": "O",
                    "explanation": "수요는 구매하거나 이용하려는 필요와 의사를 뜻합니다.",
                },
                {
                    "type": "OX",
                    "question": "자금 수요는 기업의 금융 지원 필요와 관련될 수 있다.",
                    "answer": "O",
                    "explanation": "기사에서 자금 조달 부담과 금융 지원 필요를 다루기 때문입니다.",
                },
                {
                    "type": "OX",
                    "question": "뉴스 내용과 무관한 사실도 정답 근거로 사용할 수 있다.",
                    "answer": "X",
                    "explanation": "퀴즈는 뉴스 본문에 있는 내용만 근거로 만들어야 합니다.",
                },
            ]
        },
        ensure_ascii=False,
    )
    print(parse_quiz_response(response_text))


if __name__ == "__main__":
    print_quiz_parse_sample()

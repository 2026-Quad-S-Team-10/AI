import json
import re

try:
    from app.services.news_preprocess_service import clean_news_content
    from app.services.openai_service import call_openai_chat
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from news_preprocess_service import clean_news_content
    from openai_service import call_openai_chat


KEYWORD_EXPLANATION_FIELD = "keywordExplanation"


def generate_keyword_explanation(term: str, title: str, content: str) -> str:
    """Generate a beginner-friendly explanation of a term in news context."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")

    cleaned_content = clean_news_content(content)
    prompt = build_keyword_explanation_prompt(term, title, cleaned_content)
    response_text = call_openai_chat(prompt)

    return parse_keyword_explanation_response(response_text)


def build_keyword_explanation_prompt(term: str, title: str, content: str) -> str:
    """Build a prompt for JSON-only keyword explanation generation."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")

    return f"""
너는 경제 초급자를 위한 뉴스 학습 도우미다.
아래 뉴스 제목과 본문만 바탕으로 경제 용어를 쉽게 설명해라.

조건:
- 경제 용어의 기본 의미를 쉬운 말로 설명한다.
- 단순 사전식 정의만 쓰지 말고, 해당 뉴스에서 이 용어가 어떻게 연결되는지 설명한다.
- 뉴스 본문에 없는 내용은 만들지 않는다.
- 과장된 표현을 쓰지 않는다.
- 너무 길지 않게 2~3문장으로 작성한다.
- 반드시 JSON만 반환한다.
- 반환 JSON은 keywordExplanation 필드 하나만 가진다.
- keywordExplanation 값은 비어 있지 않은 문자열이어야 한다.
- 마크다운 코드블록, 설명 문장, 번호 목록은 쓰지 않는다.

반환 형식:
{{"keywordExplanation":"경제 용어의 기본 의미와 뉴스 속 연결성을 2~3문장으로 설명합니다."}}

경제 용어:
{term.strip()}

뉴스 제목:
{title.strip()}

뉴스 본문:
{content.strip()}
""".strip()


def parse_keyword_explanation_response(response_text: str) -> str:
    """Parse and validate a JSON keyword explanation response from GPT."""
    _validate_required_text(response_text, "response_text")

    try:
        parsed_response = json.loads(_extract_json_text(response_text))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse keyword explanation response as JSON: {exc}"
        ) from exc

    if not isinstance(parsed_response, dict):
        raise ValueError("keyword explanation response JSON must be an object.")

    explanation = parsed_response.get(KEYWORD_EXPLANATION_FIELD)
    if not isinstance(explanation, str):
        raise ValueError(
            "keyword explanation response must include "
            f"a {KEYWORD_EXPLANATION_FIELD} string."
        )

    cleaned_explanation = explanation.strip()
    if not cleaned_explanation:
        raise ValueError("keywordExplanation must not be empty.")

    return cleaned_explanation


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
        raise ValueError(
            "keyword explanation response did not include a JSON object."
        )

    return cleaned_text[start_index : end_index + 1]


def _validate_required_text(value: str, field_name: str) -> None:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} must not be empty.")


def print_keyword_explanation_parse_sample() -> None:
    """Simple smoke-test helper for local keyword explanation parsing checks."""
    response_text = json.dumps(
        {
            KEYWORD_EXPLANATION_FIELD: (
                "수요는 사람들이 어떤 상품이나 서비스를 필요로 하거나 사고자 하는 "
                "정도를 뜻합니다. 이 기사에서는 중소기업이 자금을 필요로 하는 "
                "상황이 금융 수요와 연결됩니다."
            )
        },
        ensure_ascii=False,
    )
    print(parse_keyword_explanation_response(response_text))


if __name__ == "__main__":
    print_keyword_explanation_parse_sample()

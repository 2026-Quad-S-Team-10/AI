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


SUMMARY_SENTENCE_COUNT = 3


def generate_news_summary(term: str, title: str, content: str) -> list[str]:
    """Generate a three-line beginner-friendly news summary."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")

    cleaned_content = clean_news_content(content)
    prompt = build_summary_prompt(term, title, cleaned_content)
    response_text = call_openai_chat(prompt)

    return parse_summary_response(response_text)


def build_summary_prompt(term: str, title: str, content: str) -> str:
    """Build a prompt for JSON-only three-line news summarization."""
    _validate_required_text(term, "term")
    _validate_required_text(title, "title")
    _validate_required_text(content, "content")

    return f"""
너는 경제 초급자를 위한 뉴스 학습 도우미다.
아래 뉴스 제목과 본문만 바탕으로, 경제 초급자도 이해하기 쉬운 한국어 문장으로 뉴스를 요약해라.

조건:
- 뉴스 본문에 없는 내용은 만들지 않는다.
- 과장된 표현을 쓰지 않는다.
- 경제 용어가 뉴스 내용과 어떻게 연결되는지 자연스럽게 반영한다.
- 각 문장은 하나의 완성된 문장으로 작성한다.
- 반드시 JSON만 반환한다.
- 반환 JSON은 summary 필드 하나만 가진다.
- summary는 문자열 배열이며, 정확히 3개의 문장만 포함한다.
- 마크다운 코드블록, 설명 문장, 번호 목록은 쓰지 않는다.

반환 형식:
{{"summary":["첫 번째 요약 문장","두 번째 요약 문장","세 번째 요약 문장"]}}

경제 용어:
{term.strip()}

뉴스 제목:
{title.strip()}

뉴스 본문:
{content.strip()}
""".strip()


def parse_summary_response(response_text: str) -> list[str]:
    """Parse and validate a JSON summary response from GPT."""
    _validate_required_text(response_text, "response_text")

    try:
        parsed_response = json.loads(_extract_json_text(response_text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse summary response as JSON: {exc}") from exc

    if not isinstance(parsed_response, dict):
        raise ValueError("summary response JSON must be an object.")

    summary = parsed_response.get("summary")
    if not isinstance(summary, list):
        raise ValueError("summary response must include a summary array.")

    cleaned_summary = [
        sentence.strip()
        for sentence in summary
        if isinstance(sentence, str) and sentence.strip()
    ]

    if len(cleaned_summary) != SUMMARY_SENTENCE_COUNT:
        raise ValueError(
            "summary array must include exactly "
            f"{SUMMARY_SENTENCE_COUNT} non-empty sentences."
        )

    return cleaned_summary


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
        raise ValueError("summary response did not include a JSON object.")

    return cleaned_text[start_index : end_index + 1]


def _validate_required_text(value: str, field_name: str) -> None:
    if value is None or not str(value).strip():
        raise ValueError(f"{field_name} must not be empty.")


def print_summary_parse_sample() -> None:
    """Simple smoke-test helper for local summary response parsing checks."""
    response_text = json.dumps(
        {
            "summary": [
                "수요가 늘면서 관련 금융 지원의 필요성이 커졌습니다.",
                "은행은 중소기업의 자금 부담을 줄이기 위한 프로그램을 운영합니다.",
                "이 뉴스는 경제 용어 수요가 실제 기업 금융과 연결되는 사례를 보여줍니다.",
            ]
        },
        ensure_ascii=False,
    )
    print(parse_summary_response(response_text))


if __name__ == "__main__":
    print_summary_parse_sample()

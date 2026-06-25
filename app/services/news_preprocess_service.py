import re


DEFAULT_MAX_CONTENT_LENGTH = 3000

BOILERPLATE_PATTERNS = (
    r"\[[^\]]*=\s*[가-힣]{2,5}\s*기자\s*\]",
    r"\[[^\]]*=\s*\]",
    r"Copyright\s*[^.。]*?(?:All rights reserved\.?|무단전재\s*및\s*재배포\s*금지)?",
    r"ⓒ\s*[^.。]*?(?:무단전재\s*및\s*재배포\s*금지|All rights reserved\.?)?",
    r"저작권자\s*ⓒ?\s*[^.。]*?(?:무단전재\s*및\s*재배포\s*금지)?",
    r"무단전재\s*및\s*재배포\s*금지",
    r"무단\s*전재[-·ㆍ]?\s*재배포\s*금지",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"[가-힣]{2,5}\s*기자\s*=?\s*",
    r"기자명\s*[가-힣]{2,5}\s*기자?",
    r"(?:제보|문의메일|기사제보|보도자료)\s*[:：]?\s*\S+",
    r"(?:댓글|공유|좋아요|기사저장|주요기사|추천기사|관련기사|많이 본 뉴스|인기기사)\s*",
)

CUT_OFF_PATTERNS = (
    r"Copyright\s*@?.*",
    r"Copyright\s*ⓒ.*",
    r"UPDATE\s*:\s*\d{4}년.*",
    r"무단전재\s*및\s*재배포\s*금지.*",
    r"무단\s*전재[-·ㆍ]?\s*재배포\s*금지.*",
    r"저작권자\s*ⓒ?.*",
    r"(?:댓글|공유|좋아요|기사저장|주요기사|추천기사|관련기사|많이 본 뉴스|인기기사).*$",
)

SENTENCE_END_PATTERN = re.compile(r"(?<=[.!?。！？다요죠함음됨임])\s+")


def clean_news_content(
    content: str,
    max_length: int = DEFAULT_MAX_CONTENT_LENGTH,
) -> str:
    """Return cleaned news content suitable for GPT input."""
    if content is None:
        raise ValueError("content must not be None.")

    cleaned_content = normalize_whitespace(str(content))
    if not cleaned_content:
        raise ValueError("content must not be empty.")

    cleaned_content = remove_boilerplate_text(cleaned_content)
    cleaned_content = normalize_whitespace(cleaned_content)
    cleaned_content = truncate_by_sentence(cleaned_content, max_length)
    cleaned_content = normalize_whitespace(cleaned_content)

    if not cleaned_content:
        raise ValueError("content is empty after preprocessing.")

    return cleaned_content


def remove_boilerplate_text(content: str) -> str:
    """Remove common news-site boilerplate from content."""
    cleaned_content = str(content)

    for pattern in CUT_OFF_PATTERNS:
        cleaned_content = re.sub(
            pattern,
            "",
            cleaned_content,
            flags=re.IGNORECASE | re.DOTALL,
        )

    for pattern in BOILERPLATE_PATTERNS:
        cleaned_content = re.sub(
            pattern,
            " ",
            cleaned_content,
            flags=re.IGNORECASE,
        )

    return cleaned_content


def normalize_whitespace(content: str) -> str:
    """Normalize spaces, tabs, and line breaks."""
    normalized_content = str(content).replace("\t", " ")
    normalized_content = re.sub(r"[\r\n]+", " ", normalized_content)
    normalized_content = re.sub(r"\s+", " ", normalized_content)

    return normalized_content.strip()


def truncate_by_sentence(
    content: str,
    max_length: int = DEFAULT_MAX_CONTENT_LENGTH,
) -> str:
    """Truncate content near a sentence boundary when possible."""
    if max_length <= 0:
        raise ValueError("max_length must be greater than 0.")

    normalized_content = normalize_whitespace(content)
    if len(normalized_content) <= max_length:
        return normalized_content

    candidate = normalized_content[:max_length].rstrip()
    sentence_end_index = _find_last_sentence_end(candidate)

    if sentence_end_index > 0:
        return candidate[:sentence_end_index].rstrip()

    word_boundary_index = candidate.rfind(" ")
    if word_boundary_index > 0:
        return candidate[:word_boundary_index].rstrip()

    return candidate


def _find_last_sentence_end(content: str) -> int:
    sentence_end_indexes = [
        match.end()
        for match in re.finditer(r"[.!?。！？]", content)
    ]

    korean_sentence_end_indexes = [
        match.end()
        for match in SENTENCE_END_PATTERN.finditer(content)
    ]

    sentence_end_indexes.extend(korean_sentence_end_indexes)

    if not sentence_end_indexes:
        return -1

    return max(sentence_end_indexes)


def print_clean_news_content_sample() -> None:
    """Simple smoke-test helper for local content preprocessing checks."""
    raw_content = (
        "  경제 뉴스 본문입니다.\n\n"
        "시장 수요가 증가했다는 분석입니다.\t추가 문장입니다. "
        "홍길동 기자 test@example.com Copyright @Example Corp. "
        "All rights reserved. 댓글 공유 좋아요 "
    )
    print(clean_news_content(raw_content, max_length=80))


if __name__ == "__main__":
    print_clean_news_content_sample()

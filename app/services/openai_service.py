import os


DEFAULT_OPENAI_MODEL = "gpt-5.2"


def call_openai_chat(prompt: str, max_output_tokens: int | None = None) -> str:
    """Call OpenAI Responses API and return the output text."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty.")
    if max_output_tokens is not None and max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be greater than 0.")

    _load_dotenv_if_available()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "openai package is not installed. Install dependencies from requirements.txt."
        ) from exc

    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    client = OpenAI(api_key=api_key)

    try:
        request_kwargs = {
            "model": model,
            "input": prompt,
        }
        if max_output_tokens is not None:
            request_kwargs["max_output_tokens"] = max_output_tokens

        response = client.responses.create(**request_kwargs)
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    response_text = getattr(response, "output_text", None)
    if not response_text:
        raise ValueError("OpenAI API response did not include output text.")

    return response_text


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv()

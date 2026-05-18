from fastapi import APIRouter, HTTPException

from app.schemas.news_generate_schema import (
    NewsGenerateRequest,
    NewsGenerateResponse,
)
from app.services.news_generate_service import generate_news_learning_content


router = APIRouter(prefix="/ai/news", tags=["AI News"])


@router.post(
    "/generate",
    response_model=NewsGenerateResponse,
    summary="뉴스 요약 및 퀴즈 생성",
)
def generate_news(request: NewsGenerateRequest) -> NewsGenerateResponse:
    try:
        result = generate_news_learning_content(
            term=request.term,
            difficulty=request.difficulty,
            category=request.category,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("No news found") or message.startswith("No valid news"):
            raise HTTPException(status_code=404, detail=message) from exc
        if "content" in message.lower() or "term" in message.lower():
            raise HTTPException(status_code=400, detail=message) from exc
        raise HTTPException(status_code=500, detail=message) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate news learning content: {exc}",
        ) from exc

    return NewsGenerateResponse(**result)

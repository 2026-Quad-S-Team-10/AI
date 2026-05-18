from fastapi import FastAPI

from app.routers.news_generate_router import router as news_generate_router


app = FastAPI(
    title="QuadS AI Server",
    description="AI server for news-based economy learning content.",
)

app.include_router(news_generate_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}

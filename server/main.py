"""FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .session import SessionStore
from .routers import chat, patterns

logger = logging.getLogger(__name__)


def _create_agent():
    """Instantiate the AI agent based on config."""
    from ai.agent import PatternDesignAgent

    if settings.ai_provider == "claude":
        from ai.providers.claude import ClaudeProvider
        provider = ClaudeProvider(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
        )
    else:
        from ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    return PatternDesignAgent(provider=provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sessions = SessionStore()
    app.state.agent = _create_agent()

    # Background cleanup task
    async def cleanup():
        while True:
            await asyncio.sleep(300)  # every 5 minutes
            await app.state.sessions.cleanup_expired()

    task = asyncio.create_task(cleanup())
    yield
    task.cancel()


app = FastAPI(
    title="Seamly2D AI Pattern Assistant",
    description="AI-powered sewing pattern design chatbot",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(patterns.router)

# Serve frontend static files
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

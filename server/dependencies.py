"""FastAPI dependency providers."""

from fastapi import Request

from .session import SessionStore


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.sessions


def get_agent(request: Request):
    return request.app.state.agent

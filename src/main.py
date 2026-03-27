from fastapi import FastAPI

from src.api.chat import router as chat_router
from src.auth.service import AuthService
from src.sessions.store import SessionStore

app = FastAPI(title="F1 Assistant API")
app.state.session_store = SessionStore()
app.state.auth_service = AuthService()
app.include_router(chat_router)

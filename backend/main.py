from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import models
from config import settings
from database import Base, engine
from routers import auth, chat, webmcp

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentInbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(webmcp.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "AgentInbox"}


# Frontend fayllari shu papkada: backend/static (index.html, style.css, app.js).
# CSS/JS "/static/..." prefiksi bilan so'raladi (index.html'dagi havolalarga mos),
# "/" esa index.html'ning o'zini qaytaradi.
STATIC_DIR = Path(__file__).parent / "static"

if (STATIC_DIR / "index.html").exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")
else:
    # Frontend hali qo'shilmagan bo'lsa — oddiy JSON javob.
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "service": "AgentInbox",
            "note": "frontend hali qo'shilmagan (backend/static/index.html topilmadi)",
        }

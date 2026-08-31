from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


# Sherigim frontend build'ini shu papkaga qo'yadi: backend/static
# (Vite bo'lsa vite.config.js'da build.outDir = "../backend/static" qilib qo'yish kifoya)
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    # html=True: "/" so'ralganda static/index.html qaytadi, boshqa static
    # fayllar (js/css) ham shu papkadan to'g'ridan-to'g'ri xizmat qiladi.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    # Frontend hali qo'shilmagan bo'lsa (hozirgi holat) — oddiy JSON javob.
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "service": "AgentInbox",
            "note": "frontend hali build qilib qo'yilmagan (backend/static bo'sh)",
        }

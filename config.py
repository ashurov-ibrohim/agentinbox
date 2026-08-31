from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Render'da bu qiymatni "production" qilib qo'yamiz (env variable orqali).
    # Shu flag'ga qarab cookie'ning secure=True/False bo'lishi belgilanadi (auth.py).
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: str = "http://localhost:8000/auth/callback"
    # Gemini hozircha ishlatilmayapti (deprioritized) — shuning uchun default bo'sh
    # qildik, aks holda bu qiymat .env/Render'da bo'lmasa app umuman ishga tushmaydi.
    GEMINI_API_KEY: str = ""
    SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
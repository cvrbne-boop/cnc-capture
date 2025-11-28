from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cnc:cncpass@db:5432/cnc"
    SECRET_KEY: str = "replace-me-with-secure-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24
    QR_SECRET: str = "qr-secret-change"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = "/app/.env"

settings = Settings()

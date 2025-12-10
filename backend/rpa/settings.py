"""
Configurações do projeto RPA
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # MongoDB
    MONGODB_URL: str = "mongodb+srv://pedro_db_user:0fOGUSiodZIlWpvo@lfa-db.wpr5usp.mongodb.net/?retryWrites=true&w=majority&appName=lfa-db"
    MONGODB_DB_NAME: str = "projeto_fluxlaw"
    MONGODB_COLLECTION_TASKS: str = "tasks"

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        ""
    )
    AZURE_CONTAINER_NAME: str = "documentos"

    # Local Storage (usado quando Azure não está configurado)
    USE_LOCAL_STORAGE: bool = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "downloads")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # API
    API_TITLE: str = "RPA FluxLaw API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para orquestração de tarefas de download de documentos"

    # CORS - Origens permitidas (separadas por vírgula no .env)
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000"
    ).split(",")

    # Celery Beat Schedule
    BEAT_SCHEDULE_MINUTES: int = 10

    # Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".xlsx", ".xls", ".csv"]

    # eLaw COGNA Credentials
    ELAW_USERNAME: str = os.getenv("ELAW_USERNAME", "lima.feigelson06")
    ELAW_PASSWORD: str = os.getenv("ELAW_PASSWORD", "@Ingrid74")

    # BCLegal Loft Credentials
    BCLEGAL_USER: str = os.getenv("BCLEGAL_USER", "")
    BCLEGAL_PASSWORD: str = os.getenv("BCLEGAL_PASSWORD", "")

    # Lexxy SuperSim Credentials
    LEXXY_USER: str = os.getenv("LEXXY_USER", "")
    LEXXY_PASSWORD: str = os.getenv("LEXXY_PASSWORD", "")

    # Portal Integration
    PORTAL_MONGODB_DB_NAME: str = os.getenv("PORTAL_MONGODB_DB_NAME", "portal_rpa")
    PORTAL_INTEGRATION_ENABLED: bool = os.getenv("PORTAL_INTEGRATION_ENABLED", "true").lower() == "true"
    PORTAL_BEAT_SCHEDULE_MINUTES: int = int(os.getenv("PORTAL_BEAT_SCHEDULE_MINUTES", "5"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

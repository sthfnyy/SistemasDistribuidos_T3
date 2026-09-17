import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Diretório raiz do projeto do servidor
SERVER_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Audio Processing Server"
    VERSION: str = "1.0.0"
    
    # Configurações do Banco de Dados
    # Por padrão, conecta ao PostgreSQL em localhost:5434 (mapeado pelo docker-compose)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/audiodb"
    )
    
    # Diretórios de Armazenamento
    BASE_STORAGE_DIR: Path = SERVER_ROOT / "storage"
    TRASH_DIR: Path = SERVER_ROOT / "storage" / "trash"
    
    # Servidor HTTP
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Configurações FFmpeg
    FFMPEG_BIN: str = "ffmpeg"
    FFPROBE_BIN: str = "ffprobe"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()

# Garante a existência dos diretórios base de storage e trash
settings.BASE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.TRASH_DIR.mkdir(parents=True, exist_ok=True)


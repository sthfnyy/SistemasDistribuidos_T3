import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.app.config import settings
from server.app.database.models import Base

logger = logging.getLogger(__name__)

# Configuração do Engine
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
    )
except Exception as e:
    logger.warning(f"Falha ao conectar com PostgreSQL ({e}). Usando SQLite como fallback.")
    engine = create_engine("sqlite:///server/app/database/fallback_audio.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Cria as tabelas no banco de dados se ainda não existirem."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas do banco de dados verificadas/criadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar tabelas no banco de dados: {e}")
        raise e

def get_db():
    """Dependency para obter sessão do banco nas rotas do FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


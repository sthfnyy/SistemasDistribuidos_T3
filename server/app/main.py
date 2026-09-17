import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.app.config import settings
from server.app.database.connection import init_db
from server.app.routes.audio import router as audio_router
from server.app.routes.history import router as history_router
from server.app.routes.web import router as web_router

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização do Banco de Dados
    logger.info("Inicializando conexão com banco de dados e verificando tabelas...")
    init_db()
    logger.info("Servidor de áudio pronto para receber requisições.")
    yield
    logger.info("Encerrando servidor de áudio.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Servidor FastAPI com FFmpeg e PostgreSQL para processamento de áudio em 3 camadas.",
    lifespan=lifespan,
)

# Configuração de CORS para permitir acesso de clientes locais e remotos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rotas
app.include_router(audio_router)
app.include_router(history_router)
app.include_router(web_router)

@app.get("/health", tags=["Healthcheck"])
def health_check():
    """Endpoint para verificação de status do servidor."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


#!/usr/bin/env python3
import uvicorn
import os
import sys
from pathlib import Path

# Adiciona a raiz do repositório ao sys.path para importações absolutas
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from server.app.config import settings

def main():
    print("=" * 65)
    print("   Iniciando Servidor de Processamento de Áudio (Camada 2)")
    print(f"   Banco de Dados: {settings.DATABASE_URL}")
    print(f"   Storage:        {settings.BASE_STORAGE_DIR}")
    print(f"   Trash:          {settings.TRASH_DIR}")
    print(f"   Acesse a Web:   http://{settings.HOST}:{settings.PORT}/files")
    print(f"   Documentação:   http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 65)
    
    uvicorn.run(
        "server.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

if __name__ == "__main__":
    main()


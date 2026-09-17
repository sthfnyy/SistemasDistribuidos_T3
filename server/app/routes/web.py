from pathlib import Path
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from server.app.database.connection import get_db
from server.app.database.models import Audio

router = APIRouter(tags=["Interface Web"])

templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/files", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
@router.get("/web", response_class=HTMLResponse)
def serve_files_page(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza a interface web simples para listar os arquivos armazenados,
    permitindo sua reprodução diretamente pelo navegador.
    """
    audios = db.query(Audio).filter(Audio.is_deleted == False).order_by(desc(Audio.created_at)).all()
    audios_data = [a.to_dict() for a in audios]
    
    return templates.TemplateResponse(
        request=request,
        name="files.html",
        context={
            "audios": audios_data,
        }
    )


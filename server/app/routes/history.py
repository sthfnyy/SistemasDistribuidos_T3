from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from server.app.database.connection import get_db
from server.app.database.models import Audio
from server.app.schemas import AudioResponse
from server.app.routes.audio import format_audio_response

router = APIRouter(tags=["Histórico de Áudios"])

@router.get("/audios", response_model=List[AudioResponse])
@router.get("/history", response_model=List[AudioResponse])
def list_audios(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de áudios processados no servidor, ordenados pelos mais recentes.
    """
    query = db.query(Audio)
    if not include_deleted:
        query = query.filter(Audio.is_deleted == False)
        
    audios = query.order_by(desc(Audio.created_at)).offset(skip).limit(limit).all()
    
    return [format_audio_response(a, request) for a in audios]


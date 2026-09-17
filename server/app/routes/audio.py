import uuid
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from server.app.database.connection import get_db
from server.app.database.models import Audio
from server.app.services.storage import (
    create_audio_directory,
    save_file,
    save_meta_json,
    read_meta_json,
    move_to_trash,
    calculate_checksum,
)
from server.app.services.ffmpeg import get_audio_metadata, process_audio
from server.app.services.waveform import generate_waveform
from server.app.schemas import AudioResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Processamento de Áudio"])

def build_audio_urls(request: Request, audio_id: str) -> dict:
    """Gera os URLs absolutos/relativos para download e streaming."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "original": f"{base_url}/audio/{audio_id}/original",
        "processed": f"{base_url}/audio/{audio_id}/processed",
        "waveform": f"{base_url}/audio/{audio_id}/waveform",
        "meta": f"{base_url}/audio/{audio_id}/meta",
        "details": f"{base_url}/audio/{audio_id}",
    }

def format_audio_response(audio: Audio, request: Request) -> AudioResponse:
    data = audio.to_dict()
    data["urls"] = build_audio_urls(request, audio.id)
    return AudioResponse(**data)

@router.post("/process-audio", response_model=AudioResponse)
@router.post("/audios/process", response_model=AudioResponse)
async def upload_and_process_audio(
    request: Request,
    file: UploadFile = File(...),
    processing_type: str = Form("normalize_volume"),
    speed_factor: Optional[float] = Form(1.5),
    target_bitrate: Optional[str] = Form("64k"),
    target_format: Optional[str] = Form(None),
    volume_gain: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Recebe um arquivo de áudio via HTTP, aplica o processamento com FFmpeg,
    salva em storage/{YYYY}/{MM}/{DD}/{UUID}/, gera waveform.png, meta.json
    e registra os metadados no PostgreSQL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido ou sem nome.")

    # Gera UUID único para a requisição
    audio_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Extrai nome e extensão
    original_path_obj = Path(file.filename)
    original_name = original_path_obj.name
    orig_ext = original_path_obj.suffix.lower() or ".mp3"
    if not orig_ext.startswith("."):
        orig_ext = f".{orig_ext}"

    # Cria diretório de armazenamento conforme especificação:
    # storage/{YYYY}/{MM}/{DD}/{UUID}/
    audio_dir = create_audio_directory(audio_id, now)

    # 1. Salva arquivo original: audio_original.{ext}
    orig_dest = audio_dir / f"audio_original{orig_ext}"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Arquivo enviado está vazio.")
    save_file(orig_dest, content)

    # 2. Extrai metadados do original via ffprobe
    try:
        orig_meta = get_audio_metadata(orig_dest)
    except Exception as e:
        logger.error(f"Falha na extração de metadados: {e}")
        orig_meta = {
            "duration_sec": None,
            "bitrate": None,
            "sample_rate": None,
            "channels": None,
            "size_bytes": len(content),
            "mime_type": "audio/mpeg",
        }

    # 3. Determina extensão de saída para áudio processado
    proc_ext = orig_ext
    p_type = processing_type.lower().strip()
    if p_type in ["format_conversion", "conversao_formato", "format", "conversão de formato"] and target_format:
        tf = target_format.strip().lower()
        proc_ext = f".{tf}" if not tf.startswith(".") else tf

    proc_dest = audio_dir / f"audio_processed{proc_ext}"

    # Monta dicionário de parâmetros
    processing_params = {
        "speed_factor": speed_factor,
        "target_bitrate": target_bitrate,
        "target_format": target_format,
        "volume_gain": volume_gain,
    }

    # 4. Executa processamento FFmpeg
    try:
        process_audio(
            input_path=orig_dest,
            output_path=proc_dest,
            processing_type=processing_type,
            params=processing_params,
        )
    except Exception as e:
        logger.error(f"Erro ao processar áudio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento FFmpeg: {str(e)}")

    # 5. Extrai metadados do áudio processado
    try:
        proc_meta = get_audio_metadata(proc_dest)
    except Exception as e:
        logger.warning(f"Não foi possível extrair metadados do processado: {e}")
        proc_meta = {
            "duration_sec": orig_meta.get("duration_sec"),
            "bitrate": None,
            "sample_rate": orig_meta.get("sample_rate"),
            "channels": orig_meta.get("channels"),
            "size_bytes": proc_dest.stat().st_size if proc_dest.exists() else 0,
            "mime_type": orig_meta.get("mime_type"),
        }

    # 6. Gera waveform.png a partir do áudio processado
    waveform_dest = audio_dir / "waveform.png"
    try:
        generate_waveform(proc_dest, waveform_dest)
        path_waveform_str = str(waveform_dest)
    except Exception as e:
        logger.warning(f"Erro ao gerar waveform: {e}")
        path_waveform_str = None

    # 7. Calcula checksums e gera meta.json
    checksum_orig = calculate_checksum(orig_dest)
    checksum_proc = calculate_checksum(proc_dest)

    meta_json_data = {
        "id": audio_id,
        "original_name": original_name,
        "created_at": now.isoformat(),
        "processing_type": processing_type,
        "processing_params": processing_params,
        "original": {
            "file_name": orig_dest.name,
            "size_bytes": orig_meta.get("size_bytes"),
            "checksum_sha256": checksum_orig,
            "duration_sec": orig_meta.get("duration_sec"),
            "sample_rate": orig_meta.get("sample_rate"),
            "channels": orig_meta.get("channels"),
            "bitrate": orig_meta.get("bitrate"),
            "mime_type": orig_meta.get("mime_type"),
        },
        "processed": {
            "file_name": proc_dest.name,
            "size_bytes": proc_meta.get("size_bytes"),
            "checksum_sha256": checksum_proc,
            "duration_sec": proc_meta.get("duration_sec"),
            "sample_rate": proc_meta.get("sample_rate"),
            "channels": proc_meta.get("channels"),
            "bitrate": proc_meta.get("bitrate"),
            "mime_type": proc_meta.get("mime_type"),
        },
        "waveform": waveform_dest.name if waveform_dest.exists() else None,
    }
    save_meta_json(audio_dir, meta_json_data)

    # 8. Registra no PostgreSQL via SQLAlchemy
    db_audio = Audio(
        id=audio_id,
        original_name=original_name,
        original_ext=orig_ext,
        mime_type=orig_meta.get("mime_type") or "audio/mpeg",
        size_bytes=orig_meta.get("size_bytes") or len(content),
        duration_sec=proc_meta.get("duration_sec") or orig_meta.get("duration_sec"),
        sample_rate=proc_meta.get("sample_rate") or orig_meta.get("sample_rate"),
        channels=proc_meta.get("channels") or orig_meta.get("channels"),
        bitrate=proc_meta.get("bitrate") or orig_meta.get("bitrate"),
        processing_type=processing_type,
        processing_params=json.dumps(processing_params, ensure_ascii=False),
        created_at=now,
        path_original=str(orig_dest),
        path_processed=str(proc_dest),
        path_waveform=path_waveform_str,
        is_deleted=False,
    )

    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)

    logger.info(f"Áudio {audio_id} processado e registrado com sucesso.")
    return format_audio_response(db_audio, request)

@router.get("/audio/{uuid_str}", response_model=AudioResponse)
@router.get("/audios/{uuid_str}", response_model=AudioResponse)
def get_audio_details(
    uuid_str: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Busca os detalhes e metadados de um áudio específico por UUID."""
    audio = db.query(Audio).filter(Audio.id == uuid_str, Audio.is_deleted == False).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado.")
    return format_audio_response(audio, request)

@router.get("/audio/{uuid_str}/original")
@router.get("/download/original/{uuid_str}")
def download_original(
    uuid_str: str,
    db: Session = Depends(get_db)
):
    """Retorna o áudio original armazenado."""
    audio = db.query(Audio).filter(Audio.id == uuid_str).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado no banco.")
    
    file_path = Path(audio.path_original)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo original não encontrado no disco.")
        
    return FileResponse(
        path=str(file_path),
        media_type=audio.mime_type,
        filename=f"original_{audio.original_name}"
    )

@router.get("/audio/{uuid_str}/processed")
@router.get("/download/processed/{uuid_str}")
def download_processed(
    uuid_str: str,
    db: Session = Depends(get_db)
):
    """Retorna o áudio processado para download ou streaming."""
    audio = db.query(Audio).filter(Audio.id == uuid_str).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado no banco.")
    
    file_path = Path(audio.path_processed)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo processado não encontrado no disco.")

    # Identifica mime type do arquivo processado
    proc_mime = audio.mime_type
    return FileResponse(
        path=str(file_path),
        media_type=proc_mime,
        filename=f"processed_{audio.original_name}"
    )

@router.get("/audio/{uuid_str}/waveform")
@router.get("/download/waveform/{uuid_str}")
def download_waveform(
    uuid_str: str,
    db: Session = Depends(get_db)
):
    """Retorna a imagem da forma de onda gerada (waveform.png)."""
    audio = db.query(Audio).filter(Audio.id == uuid_str).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado.")
    
    if not audio.path_waveform:
        raise HTTPException(status_code=404, detail="Waveform não disponível.")

    waveform_path = Path(audio.path_waveform)
    if not waveform_path.exists():
        raise HTTPException(status_code=404, detail="Imagem da waveform não encontrada no disco.")

    return FileResponse(
        path=str(waveform_path),
        media_type="image/png",
        filename=f"waveform_{audio.id}.png"
    )

@router.get("/audio/{uuid_str}/meta")
def get_meta_file(
    uuid_str: str,
    db: Session = Depends(get_db)
):
    """Retorna o conteúdo do arquivo meta.json."""
    audio = db.query(Audio).filter(Audio.id == uuid_str).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado.")

    audio_dir = Path(audio.path_original).parent
    meta = read_meta_json(audio_dir)
    if not meta:
        raise HTTPException(status_code=404, detail="meta.json não encontrado no disco.")
        
    return JSONResponse(content=meta)

@router.delete("/audio/{uuid_str}")
def delete_audio(
    uuid_str: str,
    db: Session = Depends(get_db)
):
    """
    Remove o áudio do histórico ativo, movendo seus arquivos para a pasta trash/
    e marcando is_deleted=True no banco.
    """
    audio = db.query(Audio).filter(Audio.id == uuid_str).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado.")

    # Move os arquivos para o diretório trash/
    audio_dir = Path(audio.path_original).parent
    try:
        trash_path = move_to_trash(audio_dir, audio.id)
        audio.is_deleted = True
        audio.path_original = str(trash_path / Path(audio.path_original).name)
        audio.path_processed = str(trash_path / Path(audio.path_processed).name)
        if audio.path_waveform:
            audio.path_waveform = str(trash_path / Path(audio.path_waveform).name)
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao mover áudio para a lixeira: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao excluir áudio: {str(e)}")

    return {"message": f"Áudio {uuid_str} movido para a lixeira com sucesso."}


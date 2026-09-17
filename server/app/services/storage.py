import os
import shutil
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from server.app.config import settings

def calculate_checksum(file_path: Path) -> str:
    """Calcula o checksum SHA-256 de um arquivo."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_audio_directory(audio_id: str, dt: Optional[datetime] = None) -> Path:
    """
    Retorna o caminho da pasta para um áudio específico organizado por data:
    storage/{YYYY}/{MM}/{DD}/{UUID}/
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    
    year = dt.strftime("%Y")
    month = dt.strftime("%m")
    day = dt.strftime("%d")
    
    target_dir = settings.BASE_STORAGE_DIR / year / month / day / audio_id
    return target_dir

def create_audio_directory(audio_id: str, dt: Optional[datetime] = None) -> Path:
    """Cria e retorna a estrutura de diretórios para o áudio."""
    target_dir = get_audio_directory(audio_id, dt)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def save_file(target_path: Path, content: bytes) -> Path:
    """Salva bytes em um arquivo de destino."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "wb") as f:
        f.write(content)
    return target_path

def save_meta_json(audio_dir: Path, meta_data: Dict[str, Any]) -> Path:
    """Grava o arquivo meta.json na pasta do áudio."""
    meta_path = audio_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=4, ensure_ascii=False)
    return meta_path

def read_meta_json(audio_dir: Path) -> Optional[Dict[str, Any]]:
    """Lê o arquivo meta.json da pasta do áudio se existir."""
    meta_path = audio_dir / "meta.json"
    if not meta_path.exists():
        return None
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

def move_to_trash(audio_dir: Path, audio_id: str) -> Path:
    """
    Move a pasta de um áudio para o diretório trash/ temporário.
    """
    settings.TRASH_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trash_target = settings.TRASH_DIR / f"{audio_id}_{timestamp}"
    
    if audio_dir.exists():
        shutil.move(str(audio_dir), str(trash_target))
        return trash_target
    else:
        raise FileNotFoundError(f"Diretório não encontrado para exclusão: {audio_dir}")


import os
import sys
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configura conexão com o PostgreSQL em execução no Docker
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5434/audiodb"

from server.app.main import app
from server.app.database.connection import init_db, SessionLocal
from server.app.database.models import Audio

@pytest.fixture(scope="session", autouse=True)
def init_postgres():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_audio(tmp_path):
    wav_path = tmp_path / "postgres_sample.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "sine=frequency=500:duration=1.5",
        str(wav_path)
    ], capture_output=True, check=True)
    return wav_path

def test_postgres_upload_and_persistence(client, sample_audio):
    # Envia o áudio via POST para o endpoint
    with open(sample_audio, "rb") as f:
        res = client.post(
            "/process-audio",
            files={"file": ("tone_500hz.wav", f, "audio/wav")},
            data={"processing_type": "normalize_volume"}
        )
    assert res.status_code == 200
    data = res.json()
    audio_id = data["id"]
    assert audio_id is not None

    # Consulta diretamente via sessão SQLAlchemy no PostgreSQL
    db = SessionLocal()
    try:
        db_audio = db.query(Audio).filter(Audio.id == audio_id).first()
        assert db_audio is not None
        assert db_audio.original_name == "tone_500hz.wav"
        assert db_audio.processing_type == "normalize_volume"
        assert db_audio.duration_sec is not None
        assert db_audio.size_bytes > 0
        assert Path(db_audio.path_original).exists()
        assert Path(db_audio.path_processed).exists()
        assert Path(db_audio.path_waveform).exists()
    finally:
        db.close()

    # Consulta via endpoint GET /audios
    res_list = client.get("/audios")
    assert res_list.status_code == 200
    assert any(a["id"] == audio_id for a in res_list.json())


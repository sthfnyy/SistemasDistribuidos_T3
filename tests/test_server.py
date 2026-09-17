import os
import sys
import subprocess
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configura banco de dados em memória ou arquivo temporário para testes isolados
os.environ["DATABASE_URL"] = "sqlite:///tests_temp_audio.db"

from server.app.main import app
from server.app.database.connection import init_db, engine
from server.app.database.models import Base
from server.app.services.ffmpeg import get_audio_metadata, process_audio
from server.app.services.waveform import generate_waveform
from server.app.services.storage import calculate_checksum

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if Path("tests_temp_audio.db").exists():
        Path("tests_temp_audio.db").unlink()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_wav(tmp_path):
    """Gera um arquivo de áudio WAV sintético de 2 segundos para os testes."""
    wav_path = tmp_path / "sample.wav"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=2",
        str(wav_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return wav_path

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ffmpeg_metadata_extraction(sample_wav):
    meta = get_audio_metadata(sample_wav)
    assert meta["duration_sec"] is not None
    assert meta["duration_sec"] >= 1.9
    assert meta["channels"] == 1
    assert meta["sample_rate"] == 44100
    assert meta["size_bytes"] > 0

def test_ffmpeg_normalize_volume(sample_wav, tmp_path):
    out = tmp_path / "norm.wav"
    result = process_audio(sample_wav, out, "normalize_volume")
    assert out.exists()
    assert out.stat().st_size > 0

def test_ffmpeg_mono_conversion(sample_wav, tmp_path):
    out = tmp_path / "mono.wav"
    result = process_audio(sample_wav, out, "mono")
    assert out.exists()
    meta = get_audio_metadata(out)
    assert meta["channels"] == 1

def test_ffmpeg_bitrate_reduction(sample_wav, tmp_path):
    out = tmp_path / "low_bitrate.mp3"
    result = process_audio(sample_wav, out, "bitrate", {"target_bitrate": "64k"})
    assert out.exists()
    assert out.stat().st_size > 0

def test_ffmpeg_format_conversion(sample_wav, tmp_path):
    out = tmp_path / "converted.mp3"
    result = process_audio(sample_wav, out, "format_conversion")
    assert out.exists()
    meta = get_audio_metadata(out)
    assert meta["mime_type"] == "audio/mpeg"

def test_ffmpeg_speed_change(sample_wav, tmp_path):
    out = tmp_path / "speed.wav"
    result = process_audio(sample_wav, out, "speed", {"speed_factor": 1.5})
    assert out.exists()
    meta = get_audio_metadata(out)
    # A duração deve ter caído aproximadamente para 2 / 1.5 ~= 1.33s
    assert meta["duration_sec"] < 1.7

def test_waveform_generation(sample_wav, tmp_path):
    png_out = tmp_path / "waveform.png"
    res = generate_waveform(sample_wav, png_out)
    assert png_out.exists()
    assert png_out.stat().st_size > 0

def test_full_upload_and_process_flow(client, sample_wav):
    with open(sample_wav, "rb") as f:
        files = {"file": ("test_music.wav", f, "audio/wav")}
        data = {
            "processing_type": "normalize_volume"
        }
        response = client.post("/process-audio", files=files, data=data)
    
    assert response.status_code == 200
    audio_data = response.json()
    audio_id = audio_data["id"]
    assert audio_data["original_name"] == "test_music.wav"
    assert audio_data["processing_type"] == "normalize_volume"
    assert audio_data["urls"]["original"] is not None

    # Verifica busca de detalhes
    res_details = client.get(f"/audio/{audio_id}")
    assert res_details.status_code == 200
    assert res_details.json()["id"] == audio_id

    # Verifica download original
    res_orig = client.get(f"/audio/{audio_id}/original")
    assert res_orig.status_code == 200
    assert len(res_orig.content) > 0

    # Verifica download processado
    res_proc = client.get(f"/audio/{audio_id}/processed")
    assert res_proc.status_code == 200
    assert len(res_proc.content) > 0

    # Verifica download waveform
    res_wave = client.get(f"/audio/{audio_id}/waveform")
    assert res_wave.status_code == 200
    assert res_wave.headers["content-type"] == "image/png"

    # Verifica meta.json
    res_meta = client.get(f"/audio/{audio_id}/meta")
    assert res_meta.status_code == 200
    meta_json = res_meta.json()
    assert meta_json["id"] == audio_id
    assert "original" in meta_json
    assert "processed" in meta_json

    # Verifica listagem no histórico
    res_history = client.get("/audios")
    assert res_history.status_code == 200
    history_list = res_history.json()
    assert any(a["id"] == audio_id for a in history_list)

    # Verifica renderização da página HTML /files
    res_web = client.get("/files")
    assert res_web.status_code == 200
    assert "test_music.wav" in res_web.text

    # Testa exclusão / movimentação para a pasta trash/
    res_del = client.delete(f"/audio/{audio_id}")
    assert res_del.status_code == 200
    
    # Após deletar, não deve aparecer em /audios ativo
    res_hist_after = client.get("/audios")
    assert not any(a["id"] == audio_id for a in res_hist_after.json())

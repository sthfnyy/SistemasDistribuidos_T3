import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
CLIENT_DIR = ROOT_DIR / "client"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(CLIENT_DIR))

from server.app.main import app
from server.app.database.connection import init_db
from client.audio.metadata import get_audio_metadata
from client.api.client import send_audio, get_history, download_processed_audio, download_waveform

SAMPLE_AUDIO = CLIENT_DIR / "tests" / "audios" / "kontraa-water-afro-pop-music-445661.mp3"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


def test_end_to_end_client_server_integration(monkeypatch):
    """
    Testa a integração de ponta a ponta entre o cliente (api/client.py)
    e o servidor (FastAPI + FFmpeg + PostgreSQL).
    """
    client = TestClient(app)

    # Monkeypatch requests para direcionar as chamadas do cliente diretamente ao TestClient
    def mock_post(url, files=None, data=None, timeout=None):
        path = url.split("8000")[-1] if "8000" in url else url
        return client.post(path, files=files, data=data)

    def mock_get(url, stream=False, timeout=None):
        path = url.split("8000")[-1] if "8000" in url else url
        return client.get(path)

    import client.api.client as api_client
    monkeypatch.setattr(api_client.requests, "post", mock_post)
    monkeypatch.setattr(api_client.requests, "get", mock_get)

    # 1. Extrai metadados locais no cliente
    meta_local = get_audio_metadata(str(SAMPLE_AUDIO))
    assert meta_local["name"] == "kontraa-water-afro-pop-music-445661.mp3"

    # 2. Envia áudio para o servidor solicitando normalização de volume
    res_upload = send_audio(str(SAMPLE_AUDIO), "normalize_volume")
    assert "error" not in res_upload
    audio_id = res_upload["id"]
    assert audio_id is not None
    assert res_upload["processing_type"] == "normalize_volume"

    # 3. Consulta histórico pelo cliente
    history = get_history()
    assert isinstance(history, list)
    assert any(item["id"] == audio_id for item in history)

    # 4. Baixa áudio processado para pasta temporária do cliente
    with tempfile.TemporaryDirectory() as tmpdir:
        proc_dest = Path(tmpdir) / "test_processed.mp3"
        dl_proc = download_processed_audio(res_upload["urls"]["processed"], str(proc_dest))
        assert dl_proc.get("success") is True
        assert proc_dest.exists()
        assert proc_dest.stat().st_size > 0

        # 5. Baixa waveform gerada pelo servidor
        wave_dest = Path(tmpdir) / "test_waveform.png"
        dl_wave = download_waveform(res_upload["urls"]["waveform"], str(wave_dest))
        assert dl_wave.get("success") is True
        assert wave_dest.exists()
        assert wave_dest.stat().st_size > 0


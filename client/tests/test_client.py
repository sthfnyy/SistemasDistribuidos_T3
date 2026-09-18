import os
import sys
from pathlib import Path
import pytest

# Adiciona caminhos ao sys.path
CLIENT_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = CLIENT_DIR.parent
sys.path.insert(0, str(CLIENT_DIR))
sys.path.insert(0, str(ROOT_DIR))

from audio.metadata import get_audio_metadata
from audio.player import AudioPlayer
from api.client import check_server, get_history, send_audio

SAMPLE_AUDIO = CLIENT_DIR / "tests" / "audios" / "kontraa-water-afro-pop-music-445661.mp3"


def test_client_metadata_extraction():
    assert SAMPLE_AUDIO.exists()
    meta = get_audio_metadata(str(SAMPLE_AUDIO))
    assert "error" not in meta
    assert meta["name"] == "kontraa-water-afro-pop-music-445661.mp3"
    assert meta["extension"] == ".mp3"
    assert meta["duration"] > 0
    assert meta["sample_rate"] == 44100
    assert meta["channels"] == 2


def test_client_metadata_nonexistent_file():
    meta = get_audio_metadata("/caminho/falso/nao_existe.mp3")
    assert "error" in meta


def test_client_audio_player():
    player = AudioPlayer()
    # Deve inicializar ou usar dummy sem crash
    player.play(str(SAMPLE_AUDIO))
    player.stop()
    assert not player.is_playing()


def test_main_window_headless():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()

    assert window.windowTitle() == "Sistema de Processamento de Áudio - Cliente PySide6"
    assert window.format_duration(65) == "01:05"
    assert window.format_duration(None) == "Desconhecida"

    # Testa mudança de opções de processamento
    window.processing_combo.setCurrentText("Alterar velocidade")
    assert not window.extra_param_combo.isHidden()
    window.processing_combo.setCurrentText("Converter para mono")
    assert window.extra_param_combo.isHidden()


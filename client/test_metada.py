import sys
from pathlib import Path
from audio.metadata import get_audio_metadata

sample = Path(__file__).resolve().parent / "tests" / "audios" / "kontraa-water-afro-pop-music-445661.mp3"
arquivo = sys.argv[1] if len(sys.argv) > 1 else str(sample)

dados = get_audio_metadata(arquivo)
print("Metadados:", dados)
import subprocess
import logging
from pathlib import Path
from server.app.config import settings

logger = logging.getLogger(__name__)

def generate_waveform(audio_path: Path, output_image_path: Path, width: int = 800, height: int = 200, color: str = "#2563eb") -> Path:
    """
    Gera automaticamente a imagem da forma de onda (waveform.png) a partir do áudio
    utilizando o filtro de visualização nativo do FFmpeg (showwavespic).
    """
    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Monta comando FFmpeg com showwavespic e -update 1
    filter_graph = f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors={color}"
    cmd = [
        settings.FFMPEG_BIN,
        "-y",
        "-i", str(audio_path),
        "-filter_complex", filter_graph,
        "-frames:v", "1",
        "-update", "1",
        str(output_image_path)
    ]
    
    logger.info(f"Gerando waveform: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao gerar waveform com FFmpeg: {e.stderr}")
        raise RuntimeError(f"Falha na geração de waveform: {e.stderr}")
        
    return output_image_path


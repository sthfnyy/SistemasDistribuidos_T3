import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from server.app.config import settings

logger = logging.getLogger(__name__)

MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
    ".wma": "audio/x-ms-wma",
}

def get_mime_type(extension: str) -> str:
    """Retorna o tipo MIME baseado na extensão do arquivo."""
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return MIME_TYPES.get(ext, "application/octet-stream")

def get_audio_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extrai informações detalhadas do áudio usando ffprobe:
    duração, bitrate, sample rate, canais e tamanho em bytes.
    """
    cmd = [
        settings.FFPROBE_BIN,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar ffprobe em {file_path}: {e.stderr}")
        raise RuntimeError(f"Falha ao inspecionar áudio com ffprobe: {e.stderr}")
    except Exception as e:
        logger.error(f"Erro inesperado no ffprobe: {e}")
        raise RuntimeError(f"Erro na extração de metadados: {e}")

    # Localiza o stream de áudio
    audio_stream = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            audio_stream = s
            break

    format_info = data.get("format", {})
    
    # Extração de campos
    duration = None
    if audio_stream and "duration" in audio_stream and audio_stream["duration"] is not None:
        try:
            duration = float(audio_stream["duration"])
        except (ValueError, TypeError):
            duration = None
    if duration is None and "duration" in format_info:
        try:
            duration = float(format_info["duration"])
        except (ValueError, TypeError):
            duration = None

    bitrate = None
    if audio_stream and "bit_rate" in audio_stream and audio_stream["bit_rate"] is not None:
        try:
            bitrate = int(audio_stream["bit_rate"])
        except (ValueError, TypeError):
            bitrate = None
    if bitrate is None and "bit_rate" in format_info:
        try:
            bitrate = int(format_info["bit_rate"])
        except (ValueError, TypeError):
            bitrate = None

    sample_rate = None
    if audio_stream and "sample_rate" in audio_stream and audio_stream["sample_rate"] is not None:
        try:
            sample_rate = int(audio_stream["sample_rate"])
        except (ValueError, TypeError):
            sample_rate = None

    channels = None
    if audio_stream and "channels" in audio_stream and audio_stream["channels"] is not None:
        try:
            channels = int(audio_stream["channels"])
        except (ValueError, TypeError):
            channels = None

    size_bytes = file_path.stat().st_size

    return {
        "duration_sec": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
        "size_bytes": size_bytes,
        "mime_type": get_mime_type(file_path.suffix),
    }

def process_audio(
    input_path: Path,
    output_path: Path,
    processing_type: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executa o processamento de áudio solicitado via FFmpeg.
    Suporta:
      - normalize_volume / normalizacao: normalização de loudness (EBU R128)
      - mono / conversao_mono: conversão para canal único
      - speed / velocidade: alteração de velocidade (ex: 1.5x)
      - bitrate / reducao_bitrate: redução de bitrate (ex: 64k)
      - format_conversion / formato: conversão de formato (MP3, WAV, etc.)
    """
    if params is None:
        params = {}

    cmd = [settings.FFMPEG_BIN, "-y", "-i", str(input_path)]
    p_type = processing_type.lower().strip()

    # Normalização de Volume
    if p_type in ["normalize_volume", "normalizacao", "volume_normalization", "normalização de volume"]:
        # Filtro loudnorm EBU R128 padrão para streaming
        cmd.extend(["-af", "loudnorm=I=-16:TP=-1.5:LRA=11"])

    # Conversão para Mono
    elif p_type in ["mono", "conversao_mono", "to_mono", "conversão para mono"]:
        cmd.extend(["-ac", "1"])

    # Alteração de Velocidade
    elif p_type in ["speed", "alteracao_velocidade", "change_speed", "alteração da velocidade de reprodução", "velocidade"]:
        speed_factor = float(params.get("speed_factor", 1.5))
        # O filtro atempo do ffmpeg aceita valores entre 0.5 e 2.0.
        # Para valores fora desse limite, pode-se encadear filtros se necessário.
        if speed_factor < 0.5:
            cmd.extend(["-af", f"atempo=0.5,atempo={speed_factor / 0.5}"])
        elif speed_factor > 2.0:
            cmd.extend(["-af", f"atempo=2.0,atempo={speed_factor / 2.0}"])
        else:
            cmd.extend(["-af", f"atempo={speed_factor}"])

    # Redução da taxa de bits (bitrate)
    elif p_type in ["bitrate", "reducao_bitrate", "reduce_bitrate", "redução da taxa de bits"]:
        target_bitrate = params.get("target_bitrate", "64k")
        if isinstance(target_bitrate, int):
            target_bitrate = f"{target_bitrate}k"
        cmd.extend(["-b:a", str(target_bitrate)])

    # Conversão de formato
    elif p_type in ["format_conversion", "conversao_formato", "format", "conversão de formato"]:
        # A extensão do output_path já define o formato alvo
        pass

    else:
        logger.warning(f"Tipo de processamento desconhecido: {processing_type}. Aplicando cópia padrão.")

    # Adiciona o arquivo de saída
    cmd.append(str(output_path))

    logger.info(f"Executando FFmpeg: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro na execução do FFmpeg: {e.stderr}")
        raise RuntimeError(f"FFmpeg falhou ao processar áudio: {e.stderr}")

    return {
        "command": cmd,
        "processing_type": processing_type,
        "params": params,
    }


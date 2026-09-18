import os
import requests

from config.settings import API_URL


def _write_response_chunks(response, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as file:
        if hasattr(response, "iter_content"):
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        elif hasattr(response, "iter_bytes"):
            for chunk in response.iter_bytes():
                if chunk:
                    file.write(chunk)
        else:
            file.write(response.content)


def send_audio(file_path, processing_type, **extra_params):
    url = f"{API_URL}/audios/process"

    try:
        with open(file_path, "rb") as audio_file:
            files = {
                "file": audio_file
            }

            data = {
                "processing_type": processing_type
            }
            for k, v in extra_params.items():
                if v is not None:
                    data[k] = str(v)

            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=120
            )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        return {
            "error": "Servidor indisponível. Verifique se a API está executando."
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e)
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def get_history():
    url = f"{API_URL}/history"

    try:
        response = requests.get(
            url,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        return {
            "error": str(e)
        }


def get_audio_details(audio_id):
    url = f"{API_URL}/audio/{audio_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def download_original_audio(audio_id_or_url, output_path):
    if audio_id_or_url.startswith("http://") or audio_id_or_url.startswith("https://"):
        url = audio_id_or_url
    else:
        url = f"{API_URL}/audio/{audio_id_or_url}/original"

    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        _write_response_chunks(response, output_path)

        return {
            "success": True,
            "path": output_path
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def download_processed_audio(processed_url, output_path):
    if not (processed_url.startswith("http://") or processed_url.startswith("https://")):
        processed_url = f"{API_URL}/audio/{processed_url}/processed"

    try:
        response = requests.get(
            processed_url,
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        _write_response_chunks(response, output_path)

        return {
            "success": True,
            "path": output_path
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def download_waveform(audio_id_or_url, output_path):
    if audio_id_or_url.startswith("http://") or audio_id_or_url.startswith("https://"):
        url = audio_id_or_url
    else:
        url = f"{API_URL}/audio/{audio_id_or_url}/waveform"

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        _write_response_chunks(response, output_path)

        return {
            "success": True,
            "path": output_path
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def check_server():
    url = f"{API_URL}/health"

    try:
        response = requests.get(
            url,
            timeout=3
        )
        return response.status_code == 200

    except Exception:
        return False
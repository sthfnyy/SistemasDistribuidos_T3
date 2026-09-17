import os
import requests

from config.settings import API_URL


def send_audio(file_path, processing_type):

    url = f"{API_URL}/audios/process"

    try:

        with open(file_path, "rb") as audio_file:

            files = {
                "file": audio_file
            }

            data = {
                "processing_type": processing_type
            }

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
            "error":
            "Servidor indisponível. Verifique se a API está executando."
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

    # Rota correta do servidor da Pessoa 2
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


def download_processed_audio(
    processed_url,
    output_path
):

    try:

        response = requests.get(
            processed_url,
            stream=True,
            timeout=120
        )

        response.raise_for_status()

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True
        )

        with open(output_path, "wb") as file:

            for chunk in response.iter_content(
                chunk_size=8192
            ):

                if chunk:

                    file.write(chunk)

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
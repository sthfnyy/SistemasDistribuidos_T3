import os

from mutagen import File


def get_audio_metadata(file_path):

    try:

        audio = File(file_path)

        if audio is None:
            return {
                "error": "Formato não suportado"
            }


        metadata = {

            "name": os.path.basename(file_path),

            "extension":
                os.path.splitext(file_path)[1],

            "size_bytes":
                os.path.getsize(file_path),

            "duration":
                audio.info.length,

            "sample_rate":
                getattr(
                    audio.info,
                    "sample_rate",
                    None
                ),

            "channels":
                getattr(
                    audio.info,
                    "channels",
                    None
                )
        }


        return metadata


    except Exception as e:

        return {
            "error": str(e)
        }
from audio.metadata import get_audio_metadata


arquivo = "/caminho/do/seu/audio.mp3"


dados = get_audio_metadata(
    arquivo
)


print(dados)
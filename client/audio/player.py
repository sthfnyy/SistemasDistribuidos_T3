import os
import pygame


class AudioPlayer:

    def __init__(self):
        self.initialized = False
        self._init_mixer()

    def _init_mixer(self):
        try:
            pygame.mixer.init()
            self.initialized = True
        except Exception:
            try:
                # Tenta inicializar com driver dummy se ALSA/PulseAudio falhar
                os.environ["SDL_AUDIODRIVER"] = "dummy"
                pygame.mixer.init()
                self.initialized = True
            except Exception:
                self.initialized = False

    def play(self, file_path):
        if not self.initialized:
            self._init_mixer()

        if self.initialized:
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Erro ao reproduzir áudio: {e}")

    def stop(self):
        if self.initialized:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def is_playing(self):
        if self.initialized:
            try:
                return pygame.mixer.music.get_busy()
            except Exception:
                return False
        return False
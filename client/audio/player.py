import pygame


class AudioPlayer:

    def __init__(self):

        pygame.mixer.init()


    def play(self, file_path):

        pygame.mixer.music.load(
            file_path
        )

        pygame.mixer.music.play()


    def stop(self):

        pygame.mixer.music.stop()


    def is_playing(self):

        return pygame.mixer.music.get_busy()
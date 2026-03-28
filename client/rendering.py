"""Display/surface setup for the rebuilt race client."""

import pygame


class Renderer:
    def __init__(self, constants):
        self.C = constants
        self.screen = pygame.display.set_mode((self.C.WIDTH, self.C.HEIGHT))
        pygame.display.set_caption("Nested Rectangle Wager Racer")

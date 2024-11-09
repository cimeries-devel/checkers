import pygame


class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()

    def initial_data(self, square_size, crown, grey):
        self.square_size = square_size
        self.crown = crown
        self.grey = grey

    def calc_pos(self):
        self.x = self.square_size * self.col + self.square_size // 2
        self.y = self.square_size * self.row + self.square_size // 2

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = self.square_size // 2 - self.PADDING
        pygame.draw.circle(win, self.grey, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            win.blit(self.crown, (self.x - self.crown.get_width() // 2, self.y - self.crown.get_height() // 2))

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()

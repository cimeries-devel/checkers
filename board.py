import pygame
from piece import Piece


class Board:
    def __init__(self, black, red, rows, cols, white, square_size):
        self.black = black
        self.red = red
        self.rows = rows
        self.cols = cols
        self.white = white
        self.square_size = square_size
        self.board = []
        self.white_left = 12
        self.red_left = 12
        self.white_kings = 0
        self.red_kings = 0
        self.create_board()

    def draw_squares(self, win):
        win.fill(self.black)
        for row in range(self.rows):
            for col in range(row % 2, self.cols, 2):
                pygame.draw.rect(win, self.white, (row * self.square_size,
                                                   col * self.square_size,
                                                   self.square_size,
                                                   self.square_size))

    def create_board(self):
        for row in range(self.rows):
            self.board.append([])
            for col in range(self.cols):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, self.white))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, self.red))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(self.rows):
            for col in range(self.cols):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move(self, piece, row, col):
        # Mover la pieza a la nueva posición
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        # Promocionar a dama si llega al borde opuesto
        if (row == 0 and piece.color == self.red) or (row == self.rows - 1 and piece.color == self.white):
            piece.make_king()

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece.color == self.white:
                self.white_left -= 1
            else:
                self.red_left -= 1

    def evaluate(self):
        white_score = self.white_left + self.white_kings * 1.5
        red_score = self.red_left + self.red_kings * 1.5
        return white_score - red_score

    def get_all_pieces(self, color):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces

    def get_valid_moves(self, piece):
        moves = {}
        if piece.king:
            # Si es una reina, puede capturar en toda la diagonal
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, -1, piece.color))  # Arriba a la izquierda
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, 1, piece.color))   # Arriba a la derecha
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, -1, piece.color))   # Abajo a la izquierda
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, 1, piece.color))    # Abajo a la derecha
        else:
            left = piece.col - 1
            right = piece.col + 1
            row = piece.row

            if piece.color == self.white or piece.king:
                moves.update(self._traverse_left(row + 1, min(row + 3, self.rows), 1, piece.color, left))
                moves.update(self._traverse_right(row + 1, min(row + 3, self.rows), 1, piece.color, right))

            if piece.color == self.red or piece.king:
                moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
                moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))

        return moves

    def _traverse_diagonal(self, start_row, start_col, row_step, col_step, color, skipped=[]):
        moves = {}
        last = []
        row, col = start_row + row_step, start_col + col_step

        while 0 <= row < self.rows and 0 <= col < self.cols:
            current = self.board[row][col]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(row, col)] = last + skipped
                else:
                    moves[(row, col)] = last

                if last:
                    new_row = row + row_step
                    new_col = col + col_step
                    moves.update(self._traverse_diagonal(new_row, new_col, row_step, col_step, color, last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            row += row_step
            col += col_step

        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last

                if last:
                    row = r + step
                    col = left - 1
                    moves.update(self._traverse_left(row, stop, step, color, col, skipped=last))
                    col = left + 1
                    moves.update(self._traverse_right(row, stop, step, color, col, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            left -= 1

        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= self.cols:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    row = r + step
                    col = right - 1
                    moves.update(self._traverse_left(row, stop, step, color, col, skipped=last))
                    col = right + 1
                    moves.update(self._traverse_right(row, stop, step, color, col, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves

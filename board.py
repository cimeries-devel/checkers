import pygame
from piece import Piece


class Board:
    def __init__(self):
        self.board = []
        self.white_left = 12
        self.red_left = 12
        self.white_kings = 0
        self.red_kings = 0
        self.create_board()

    def draw_squares(self, win):
        win.fill(BLACK)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, WHITE, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, WHITE))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, RED))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move(self, piece, row, col):
        # Mover la pieza a la nueva posición
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)

        # Promocionar a dama si llega al borde opuesto
        if (row == 0 and piece.color == RED) or (row == ROWS - 1 and piece.color == WHITE):
            piece.make_king()

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece.color == WHITE:
                self.white_left -= 1
            else:
                self.red_left -= 1

    def evaluate(self):
        score = (self.white_left - self.red_left) + (self.white_kings - self.red_kings) * 1.8

        # Posiciones avanzadas
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    position_score = 0.1 * row if piece.color == WHITE else 0.1 * (ROWS - row - 1)
                    if piece.color == WHITE:
                        score += position_score
                    elif piece.color == RED:
                        score -= position_score

                    # Bonus de borde para protección
                    if col == 0 or col == COLS - 1:
                        score += 0.2 if piece.color == WHITE else -0.2

        return score

    def is_game_over(self):
        # El juego termina si alguno de los jugadores no tiene piezas
        if self.white_left <= 0 or self.red_left <= 0:
            return True

        # El juego también termina si ninguno de los jugadores tiene movimientos válidos
        white_moves = any(self.get_valid_moves(piece) for piece in self.get_all_pieces(WHITE))
        red_moves = any(self.get_valid_moves(piece) for piece in self.get_all_pieces(RED))
        return not white_moves or not red_moves

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
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, -1, piece.color))  # Arriba a la izquierda
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, 1, piece.color))   # Arriba a la derecha
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, -1, piece.color))   # Abajo a la izquierda
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, 1, piece.color))    # Abajo a la derecha
        else:
            left = piece.col - 1
            right = piece.col + 1
            row = piece.row

            if piece.color == WHITE or piece.king:
                moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
                moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

            if piece.color == RED or piece.king:
                moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
                moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))

        return moves

    def _traverse_diagonal(self, start_row, start_col, row_step, col_step, color, skipped=[]):
        moves = {}
        last = []
        row, col = start_row + row_step, start_col + col_step

        while 0 <= row < ROWS and 0 <= col < COLS:
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
            if right >= COLS:
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

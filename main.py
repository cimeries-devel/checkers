import pygame
import sys
import copy

# Configuración de la ventana y colores
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREY = (128, 128, 128)

# Inicializar Pygame
pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Juego de Damas con IA")

# Cargar imágenes
CROWN = pygame.transform.scale(pygame.image.load("crown.png"), (44, 25))

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

    def calc_pos(self):
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - self.PADDING
        pygame.draw.circle(win, GREY, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            win.blit(CROWN, (self.x - CROWN.get_width() // 2, self.y - CROWN.get_height() // 2))

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()

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

def alpha_beta_pruning(board, depth, alpha, beta, max_player):
    if depth == 0:
        return board.evaluate(), board

    if max_player:
        max_eval = float('-inf')
        best_move = None
        for move in get_all_moves(board, WHITE):
            evaluation, _ = alpha_beta_pruning(move, depth - 1, alpha, beta, False)
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in get_all_moves(board, RED):
            evaluation, _ = alpha_beta_pruning(move, depth - 1, alpha, beta, True)
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_all_moves(board, color):
    moves = []
    for piece in board.get_all_pieces(color):
        valid_moves = board.get_valid_moves(piece)
        for move, skip in valid_moves.items():
            temp_board = copy.deepcopy(board)
            temp_piece = temp_board.board[piece.row][piece.col]
            temp_board.move(temp_piece, move[0], move[1])
            if skip:
                temp_board.remove(skip)
            moves.append(temp_board)
    return moves

def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col

def main():
    board = Board()
    run = True
    clock = pygame.time.Clock()
    selected_piece = None
    player_turn = True  # True para el jugador (rojo), False para IA (blanco)

    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if player_turn:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = get_row_col_from_mouse(pos)
                    if selected_piece:
                        valid_moves = board.get_valid_moves(selected_piece)
                        if (row, col) in valid_moves:
                            skip = valid_moves[(row, col)]
                            board.move(selected_piece, row, col)
                            if skip:
                                board.remove(skip)  # Elimina la pieza capturada
                                # Verificar si hay otra captura disponible
                                new_valid_moves = board.get_valid_moves(selected_piece)
                                if any(new_valid_moves.values()):
                                    selected_piece = board.board[row][col]  # Mantener la pieza seleccionada para múltiples capturas
                                    continue
                            player_turn = False
                            selected_piece = None
                        else:
                            selected_piece = None
                    else:
                        piece = board.board[row][col]
                        if piece != 0 and piece.color == RED:
                            selected_piece = piece

        # Movimiento de la IA usando Alpha-Beta pruning
        if not player_turn:
            _, new_board = alpha_beta_pruning(board, 3, float('-inf'), float('inf'), True)
            board = new_board
            player_turn = True

        board.draw(WIN)
        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

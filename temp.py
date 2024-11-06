import pygame
import sys
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

# Inicializar pygame
pygame.init()

# Configuración de la ventana
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Inicializar la ventana
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Juego de Damas')

# Cargar imágenes
CROWN = pygame.transform.scale(pygame.image.load('crown.png'), (44, 25))

# Fuente para mensajes de texto
FONT = pygame.font.SysFont('Open Sans', 24)


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
        pygame.draw.circle(win, BLACK, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            win.blit(CROWN, (self.x - CROWN.getWidth() // 2, self.y - CROWN.getHeight() // 2))

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()


class Board:
    def __init__(self):
        self.board = []
        self.create_board()

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if (row + col) % 2 == 0:
                    self.board[row].append(0)
                elif row < 3:
                    self.board[row].append(Piece(row, col, RED))
                elif row > 4:
                    self.board[row].append(Piece(row, col, BLUE))
                else:
                    self.board[row].append(0)

    def draw_squares(self, win):
        win.fill(WHITE)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, BLACK, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def move(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        self.crown(piece)

    def crown(self, piece):
        if piece.color == BLUE and piece.row == 0:
            piece.make_king()
        elif piece.color == RED and piece.row == 7:
            piece.make_king()

    def get_piece(self, row, col):
        return self.board[row][col]

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0

    def valid_moves(self, piece):
        moves = {}
        if piece.king:
            moves.update(self._traverse_king(piece.row, piece.col, -1, -1))
            moves.update(self._traverse_king(piece.row, piece.col, -1, 1))
            moves.update(self._traverse_king(piece.row, piece.col, 1, -1))
            moves.update(self._traverse_king(piece.row, piece.col, 1, 1))
        else:
            left = piece.col - 1
            right = piece.col + 1
            row = piece.row

            if piece.color == BLUE:
                moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
                moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
            if piece.color == RED:
                moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
                moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))

        # Filtrar solo movimientos de captura si están disponibles
        capture_moves = {k: v for k, v in moves.items() if v}
        if capture_moves:
            return capture_moves
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
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
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
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]

            right += 1

        return moves

    def _traverse_king(self, start_row, start_col, row_step, col_step):
        moves = {}
        skipped = []
        r, c = start_row + row_step, start_col + col_step
        while 0 <= r < ROWS and 0 <= c < COLS:
            current = self.board[r][c]
            if current == 0:
                if skipped:
                    moves[(r, c)] = skipped
                else:
                    moves[(r, c)] = []
            elif current.color != self.board[start_row][start_col].color:
                if skipped:
                    break
                skipped = [current]
            else:
                break
            r += row_step
            c += col_step
        return moves

    def get_all_moves(self, color):
        all_moves = {}
        for row in self.board:
            for piece in row:
                if piece != 0 and piece.color == color:
                    moves = self.valid_moves(piece)
                    if moves:
                        all_moves[piece] = moves
        return all_moves


def get_row_col_from_mouse(pos):
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col


def draw_valid_moves(win, moves):
    for move in moves:
        row, col = move
        pygame.draw.circle(win, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)


def draw_message(win, message):
    text = FONT.render(message, True, (255, 0, 0))
    win.blit(text, (10, 10))


def computer_move(board):
    # # Definir la red bayesiana
    # model = BayesianNetwork([('Heuristic', 'Move')])
    #
    # # Definir las CPDs
    # cpd_heuristic = TabularCPD(variable='Heuristic', variable_card=2, values=[[0.5], [0.5]])
    # cpd_move = TabularCPD(variable='Move', variable_card=2,
    #                       values=[[0.8, 0.2], [0.2, 0.8]],
    #                       evidence=['Heuristic'], evidence_card=[2])
    #
    # # Agregar las CPDs al modelo
    # model.add_cpds(cpd_heuristic, cpd_move)
    #
    # # Verificar el modelo
    # assert model.check_model()
    #
    # # Realizar inferencia
    # inference = VariableElimination(model)

    all_moves = board.get_all_moves(RED)
    if not all_moves:
        return

    # Evaluar heurísticas
    move_scores = []
    for piece, moves in all_moves.items():
        for move in moves.keys():
            # Ejemplo de heurística: maximizar capturas
            score = len(moves[move])
            move_scores.append((piece, move, score))

    # Seleccionar el mejor movimiento basado en la heurística
    best_move = max(move_scores, key=lambda x: x[2])

    # Realizar el movimiento
    piece, move, _ = best_move
    board.move(piece, move[0], move[1])
    skipped = all_moves[piece][move]
    if skipped:
        board.remove(skipped)
        # Verificar si hay capturas adicionales disponibles
        valid_moves = board.valid_moves(piece)
        if valid_moves:
            computer_move(board)


def main():
    run = True
    clock = pygame.time.Clock()
    board = Board()
    selected_piece = None
    valid_moves = {}
    player_turn = True
    message = ""

    while run:
        clock.tick(60)

        if not player_turn:
            computer_move(board)
            player_turn = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and player_turn:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                if selected_piece:
                    if (row, col) in valid_moves:
                        board.move(selected_piece, row, col)
                        skipped = valid_moves[(row, col)]
                        if skipped:
                            board.remove(skipped)
                            # Verificar si hay capturas adicionales disponibles
                            valid_moves = board.valid_moves(selected_piece)
                            if valid_moves:
                                continue
                        selected_piece = None
                        valid_moves = {}
                        player_turn = False
                        message = ""
                    else:
                        selected_piece = None
                        valid_moves = {}
                        message = "Debe capturar una pieza si es posible"
                else:
                    piece = board.get_piece(row, col)
                    if piece != 0 and piece.color == BLUE:
                        selected_piece = piece
                        valid_moves = board.valid_moves(piece)

        board.draw(WIN)
        if selected_piece:
            draw_valid_moves(WIN, valid_moves)
        if message:
            draw_message(WIN, message)
        pygame.display.update()


if __name__ == "__main__":
    main()

import pygame
import sys
import copy
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

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
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
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
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    position_score = 0.1 * row if piece.color == WHITE else 0.1 * (ROWS - row - 1)
                    if piece.color == WHITE:
                        score += position_score
                    elif piece.color == RED:
                        score -= position_score
                    if col == 0 or col == COLS - 1:
                        score += 0.2 if piece.color == WHITE else -0.2
        return score

    def is_game_over(self):
        if self.white_left <= 0 or self.red_left <= 0:
            return True
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
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, -1, piece.color))
            moves.update(self._traverse_diagonal(piece.row, piece.col, -1, 1, piece.color))
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, -1, piece.color))
            moves.update(self._traverse_diagonal(piece.row, piece.col, 1, 1, piece.color))
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

decision_graph = nx.DiGraph()

def minimax(board, depth, alpha, beta, max_player, graph, node_id=0, transposition_table={}):
    board_state = tuple([tuple(row) for row in board.board])
    print(depth, alpha, beta, graph)
    if board_state in transposition_table:
        return transposition_table[board_state]

    if depth == 0 or board.is_game_over():
        score = board.evaluate()
        transposition_table[board_state] = score
        return score, board

    if max_player:
        max_eval = float('-inf')
        best_move = None
        for move in get_all_moves(board, WHITE):
            evaluation, _ = minimax(move, depth - 1, alpha, beta, False, graph, node_id + 1, transposition_table)
            graph.add_edge(node_id, node_id + 1, label=f"{evaluation:.2f}")
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        transposition_table[board_state] = (max_eval, best_move)
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for move in get_all_moves(board, RED):
            evaluation, _ = minimax(move, depth - 1, alpha, beta, True, graph, node_id + 1, transposition_table)
            graph.add_edge(node_id, node_id + 1, label=f"{evaluation:.2f}")
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        transposition_table[board_state] = (min_eval, best_move)
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

def display_decision_graph(graph):
    pos = nx.spring_layout(graph)
    labels = nx.get_edge_attributes(graph, "label")
    plt.figure(figsize=(10, 10))
    nx.draw(graph, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=8, font_weight="bold")
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=labels)

    buffer = BytesIO()
    plt.savefig(buffer, format="PNG")
    buffer.seek(0)
    plt.close()

    graph_image = pygame.image.load(buffer)
    graph_image = pygame.transform.scale(graph_image, (WIDTH, HEIGHT))
    WIN.blit(graph_image, (0, 0))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                waiting = False

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
    player_turn = True

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
                                board.remove(skip)
                                new_valid_moves = board.get_valid_moves(selected_piece)
                                if any(new_valid_moves.values()):
                                    selected_piece = board.board[row][col]
                                    continue
                            player_turn = False
                            selected_piece = None
                        else:
                            selected_piece = None
                    else:
                        piece = board.board[row][col]
                        if piece != 0 and piece.color == RED:
                            selected_piece = piece

        if board.is_game_over():
            display_decision_graph(decision_graph)
            run = False
            break

        if not player_turn:
            _, new_board = minimax(board, 4, float('-inf'), float('inf'), True, decision_graph)
            board = new_board
            player_turn = True

        board.draw(WIN)
        pygame.display.update()

    pygame.quit()
    sys.exit()

main()

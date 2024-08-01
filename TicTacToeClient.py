import os
import sys
# Redirect stderr to /dev/null to suppress macOS specific warnings
sys.stderr = open(os.devnull, 'w')

import socket
import threading
import pygame
import numpy
import random
import copy

width = 700
height = 700

# Game constants
LINE_WIDTH = 15
ROWS = 3
COLUMNS = 3
SQUARE_SIZE = width // COLUMNS
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
SPACE = SQUARE_SIZE // 4

# Colors
RED = (255, 0, 0)
BACKGROUND = (255, 255, 255)
LINE_COLOR = (23, 145, 135)
CIRCLE_COLOR = (0, 0, 255)
CROSS_COLOR = RED
MENU_BACKGROUND = (255, 255, 255)
MENU_TEXT = (0, 0, 0)


class Game_Board:
    # Same class as done in server
    def __init__(self):
        # Create a 3x3 board that is initialized with zeros
        self.board = numpy.zeros((ROWS, COLUMNS))

    def mark_square(self, row, column, player):
        # Marks the square with the player's id (1 or 2)
        self.board[row][column] = player

    def available_square(self, row, column):
        # Checks if the square is available
        return self.board[row][column] == 0

    def is_full(self):
        # Check if the game board is full
        return numpy.all(self.board != 0)

    def check_win(self, player):
        # Check if there is a vertical win
        for column in range(COLUMNS):
            if self.board[0][column] == player and self.board[1][column] == player and self.board[2][column] == player:
                return True

        # check if there is a horizontal win
        for row in range(ROWS):
            if self.board[0][row] == player and self.board[1][row] == player and self.board[2][row] == player:
                return True

        # check instances of diagonal wins
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True

        if self.board[2][0] == player and self.board[1][1] == player and self.board[0][2] == player:
            return True

        return False

    # Ai class
class AI_OPP:
    def __init__(self, level = 1, player = 2):
        # Sets the defficulty level of the AI
        self.level = level
        # Assigns the player number for the AI
        self.player = player
    def rnd(self, board):
        # Randomly chooses a random index from an empty sqaure on the game board then returns the empty square index
        empty_squares = self.get_empty_square(board)
        idx = random.randrange(0, len(empty_squares))
        return empty_squares[idx]
    def minimax(self, board, maximizing):
        # minimax algorithm will help AI for optimal move selection
        case = self.final_state(board)
        if case == 1:
            # player 1 wins will return score 1
            return 1, None
        if case == 2:
            return -1, None # Player 2 wins will return score -1
        elif self.is_full(board):
            return 0, None # Case of Draw will return score 0

        if maximizing:
            # player 1 will make moves that increase chances of winning
            max_eval = -100
            best_move = None
            empty_squares = self.get_empty_square(board)
            # Copies the board for sumulation then sumulates Player 1's
            for (row, column) in empty_squares:
                temp_board = copy.deepcopy(board)
                self.mark_square(temp_board, row, column, 1)
                #Recursively call minimax
                eval = self.minimax(temp_board, False)[0]
                #Update max evaluation and best move
                if eval > max_eval:
                    max_eval = eval
                    best_move = (row, column)
            return max_eval, best_move
        else:
            # Player 2 will make moves that decrease opponents chance of winning
            min_eval = 100
            best_move = None
            empty_squares = self.get_empty_square(board)
            for(row, column) in empty_squares:
                temp_board = copy.deepcopy(board)
                # Simulate player 2's move
                self.mark_square(temp_board, row, column, self.player)
                eval = self.minimax(temp_board, True)[0]
                if eval < min_eval:
                    min_eval = eval
                    best_move = (row, column)
            return min_eval, best_move

    def eval(self, board):
        # Evaluates the board and returns the best move based on AI level
        if self.level == 0:
            # Generate just a random move
             move = self.rnd(board)
        else:
            # Implement minimax move
            _, move = self.minimax(board, False)
        return move

    def get_empty_square(self, board):
        # Returns a list of all the empty squares on the game board
        empty_squares = []
        for row in range(ROWS):
            for column in range(COLUMNS):
                if board[row][column] == 0:
                    empty_squares.append((row, column))
        return empty_squares

    def final_state(self, board):
        # Checks the final state of the game board for winner
        for column in range(COLUMNS):
            if board[0][column] == board[1][column] == board[2][column] != 0:
                return board[0][column]
        for row in range(ROWS):
            if board[row][0] == board[row][1] == board[row][2] != 0:
                return board[row][0]
        if board[0][0] == board[1][1] == board[2][2] != 0:
            return board[1][1]
        if board[2][0] == board[1][1] == board[0][2] != 0:
            return board[1][1]
            # if no winner
        return 0

    def is_full(self, board):
        # Checks if the board is full for draw
        return not any(0 in row for row in board)

    def mark_square(self, board, row, column, player):
        # marks a square on the game board with the player's number
        board[row][column] = player

class Client:
    def __init__(self, screen, host = '192.168.86.249', port = 5555):
        # Same intialization as server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.player = int(self.client.recv(1024).decode())
        self.board = Game_Board()
        self.screen = screen
        # Indicates if playing against AI
        self.play_vs_ai = False
        # Initializes the AI OPP
        self.ai = AI_OPP()
    def send_move(self, row, column):
        # Sends the move to server
        self.client.send(f'{row}, {column}'.encode())

    def receive_move(self):
        # Receives data from server
        while True:
            data = self.client.recv(1024).decode()
            if data.startswith('win') or data == 'draw':
                print(data)
                pygame.quit()
                sys.exit()
            elif data == 'reset':
                self.board = Game_Board()
                self.screen.fill(BACKGROUND)
                draw_lines(self.screen)
                pygame.display.update()
            else:
                player, row, column = map(int, data.split(','))
                self.board.mark_square(row, column, player)
                draw_figures(self.screen, self.board.board)
                pygame.display.update()

    # Drawing Functions
def draw_text(screen, text, font, color, x, y):
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect(center=(x, y))
        screen.blit(text_obj, text_rect)

def draw_lines(screen):
        pygame.draw.line(screen, LINE_COLOR, (0, SQUARE_SIZE), (width, SQUARE_SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (0, 2 * SQUARE_SIZE), (width, 2 * SQUARE_SIZE), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE, 0), (SQUARE_SIZE, height), LINE_WIDTH)
        pygame.draw.line(screen, LINE_COLOR, (2 * SQUARE_SIZE, 0), (2 * SQUARE_SIZE, height), LINE_WIDTH)

def draw_figures(screen, board):
    for row in range(ROWS):
        for column in range(COLUMNS):
            if board[row][column] == 1:
                pygame.draw.circle(screen, CIRCLE_COLOR, (
                int(column * SQUARE_SIZE + SQUARE_SIZE // 2), int(row * SQUARE_SIZE + SQUARE_SIZE // 2)), CIRCLE_RADIUS,CIRCLE_WIDTH)

            elif board[row][column] == 2:
                pygame.draw.line(screen, CROSS_COLOR,(column * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE),(column * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SPACE), CROSS_WIDTH)
                pygame.draw.line(screen, CROSS_COLOR,(column * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE),(column * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE), CROSS_WIDTH)

# Menu screen
def menu(screen):
    menu_font = pygame.font.Font(None, 74)
    menu_running = True
    while menu_running:
        screen.fill(MENU_BACKGROUND)
        draw_text(screen, "Press '1' for Player vs AI", menu_font, MENU_TEXT, width // 2, height // 3)
        draw_text(screen, "Press '2' for Player vs Player", menu_font, MENU_TEXT, width // 2, 2 * height // 3)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return True
                elif event.key == pygame.K_2:
                    return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tic-Tac-Toe')

    play_vs_ai = menu(screen)
    screen.fill(BACKGROUND)
    draw_lines(screen)

    client = Client(screen)
    client.play_vs_ai = play_vs_ai
    player= client.player
    game_over = False

    def handle_server():
        client.receive_move()
    server_thread = threading.Thread(target=handle_server)
    server_thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over and player == client.player:
                mouseX = event.pos[0]
                mouseY = event.pos[1]

                clicked_row = int(mouseY // SQUARE_SIZE)
                clicked_column = int(mouseX // SQUARE_SIZE)

                if client.board.available_square(clicked_row, clicked_column):
                    client.send_move(clicked_row, clicked_column)
                    client.board.mark_square(clicked_row, clicked_column, client.player)
                    draw_figures(screen, client.board.board)
                    pygame.display.update()

                    if client.board.check_win(client.player):
                        print("Player Wins!")
                        game_over = True
                    elif (client.board.is_full()):
                        print("Draw!")
                        game_over = True
                    else: player = 2 if player == 1 else 1

        if client.play_vs_ai and not game_over and player == 2:
            row, column = client.ai.eval(client.board.board)
            client.board.mark_square(row, column, 2)
            draw_figures(screen, client.board.board)
            pygame.display.update()

            if client.board.check_win(2):
                print("AI wins!")
                game_over = True
            elif client.board.is_full():
                print("Draw!")
                game_over = True
            else:
                player = 1
        pygame.display.update()
if __name__ == '__main__':
    main()



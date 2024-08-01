import socket
import threading
import numpy

# Start with rows and columns constants
ROWS = 3
COLUMNS = 3

class Game_Board:
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
            if self.board[row][0] == player and self.board[row][1] == player and self.board[row][2] == player:
                return True

        # check instances of diagonal wins
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True

        if self.board[2][0] == player and self.board[1][1] == player and self.board[0][2] == player:
            return True

        return False

class Server:
    def __init__(self, host = '192.168.86.249', port = 5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to the host and the port
        self.server.bind((host, port))
        # Allow server to accept communications
        self.server.listen()
        # list of connected clients
        self.clients = []
        # intialize game board
        self.board = Game_Board()
        # Var to track current player
        self.current_player = 1

    def broadcast(self, message):
        # Sends message to all connected clients
        for client in self.clients:
             client.send(message.encode())

    def thread_client(self, client, player):
        while True:
            try:
                # Receive data from client
                data = client.recv(1024).decode()
                if data:
                    # Reset the board
                    if data == 'reset':
                        self.board = Game_Board()
                        self.current_player = 1
                        self.broadcast('reset')
                    else:
                        # Notifies all clients of the moves and in the case of a win or draw
                        row, column = map(int, data.split(','))
                        if self.board.available_square(row, column) and player == self.current_player:
                            self.board.mark_square(row, column, player)
                            self.broadcast(f"{player}, {row}, {column}")
                            if self.board.check_win(player):
                                self.broadcast(f"win, {player}")
                                self.board = Game_Board()
                            elif self.board.is_full():
                                self.broadcast("draw")
                            else:
                                self.current_player = 1 if self.current_player == 2 else 2
            except:
                # Error handling
                self.clients.remove(client)
                client.close()
                break

    def accept_client(self):
        while True:
            # Accepts a client connection and adds a client to the list
            client, addr = self.server.accept()
            self.clients.append(client)
            # Assigns a player to a number based on the order in which they connected and sends the player number to the client
            player = len(self.clients)
            client.send(str(player).encode())
            thread = threading.Thread(target=self.thread_client, args=(client, player))
            thread.start()

if __name__ == '__main__':
    server = Server()
    print("Waiting for a connection, Server Started")
    server.accept_client()
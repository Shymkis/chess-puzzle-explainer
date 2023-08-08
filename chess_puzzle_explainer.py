import chess
import chess.engine
import chess.svg
import io
import pandas as pd
import pygame
import pygame.freetype
from cairosvg import svg2png
from time import time

class Chess_Chat_GUI:
    def __init__(self, screen_width = 1080):
        # Screen
        self.screen_width = screen_width
        self.screen_ratio = 16/9
        self.screen_height = self.screen_width/self.screen_ratio
        # Chess
        self.board_size = self.screen_height
        self.margin_ratio = 3/80
        self.margin_size = self.board_size*self.margin_ratio
        self.grid_size = self.board_size - 2*self.margin_size
        # Chat
        self.chatbox_width = self.screen_width - self.board_size
        self.chat_width = self.chatbox_width - 2*self.margin_size
        self.chat_height = self.screen_height - 2*self.margin_size
        self.BLACK = (0,0,0)
        self.DARKGRAY = (64,64,64)
        self.GRAY = (128,128,128)
        self.LIGHTGRAY = (192,192,192)
        self.WHITE = (255,255,255)
        self.chats = []

    def init(self):
        # Initialize pygame
        pygame.init()
        pygame.display.set_icon(pygame.image.load("icon.svg"))
        pygame.display.set_caption("Chess Puzzle")
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        self.font = pygame.freetype.SysFont("Arial", 18)
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish_15.1_win_x64_avx2/stockfish-windows-2022-x86-64-avx2.exe")

    def quit(self):
        # Quit pygame
        self.engine.quit()
        pygame.quit()

    def create_board_image(self, board, human_color, move, from_square):
        drawing = chess.svg.board(
            board,
            orientation = chess.WHITE if human_color is None else human_color,
            lastmove = move,
            check = board.king(board.turn) if board.is_check() else None,
            fill = {from_square: "#cc0000cc"},
            size = self.board_size
        )
        f = open("board.svg", 'w')
        f.write(drawing)
        f.close()
        svg2png(url = "board.svg", write_to = "board.png")

    def display_chat(self, pad = 6, scroll_up = True, focused = True):
        pos = [self.board_size + self.margin_size + pad, self.margin_size]
        if scroll_up:
            pos[1] += self.chat_height
            for i, chat in enumerate(self.chats[::-1]):
                col = self.GRAY if focused and i != 0 else self.BLACK
                rect = self.font.get_rect(chat)
                pos[1] -= rect.height + pad
                self.font.render_to(self.screen, pos, chat, col)
        else:
            for i, chat in enumerate(self.chats):
                col = self.GRAY if focused and i + 1 != len(self.chats) else self.BLACK
                rect = self.font.render_to(self.screen, pos, chat, col)
                pos[1] += rect.height + pad

    def play_game(self, human_color = None):
        # Initialize game variables
        board = chess.Board()
        from_square = None
        move = chess.Move.null()
        if human_color is None:
            self.chats.append("CPU vs. CPU game")
        else:
            self.chats.append("You are playing as " + ("White" if human_color == chess.WHITE else "Black"))

        # Game loop
        running = True
        while running:
            # Make computer move
            if board.turn != human_color:
                move = self.engine.play(board, chess.engine.Limit(time = .5)).move
                board.push(move)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                    # Get the mouse position
                    x, y = pygame.mouse.get_pos()
                    
                    # Convert the position to chess coordinates
                    square = None
                    if x > self.margin_size and x < self.margin_size + self.grid_size and \
                        y > self.margin_size and y < self.margin_size + self.grid_size:
                        file = int((x - self.margin_size) // (self.grid_size / 8))
                        rank = int(7 - (y - self.margin_size) // (self.grid_size / 8))
                        square = chess.square(file, rank) if human_color == chess.WHITE else chess.square(7 - file, 7 - rank)
                    
                    # Determine move
                    if square is None:
                        from_square = None
                    elif from_square is None:
                        from_square = square if board.color_at(square) == board.turn else None
                    elif from_square == square:
                        from_square = None
                    else:
                        # Make the move if it's legal
                        try:
                            move = board.find_move(from_square, square)
                        except:
                            from_square = square if board.color_at(square) == board.turn else None
                        else:
                            board.push(move)
                            from_square = None
            
            # End game
            if board.is_game_over():
                running = False
                result = board.result()
                if result == "1-0":
                    self.chats.append("White wins!")
                elif result == "0-1":
                    self.chats.append("Black wins!")
                else:
                    self.chats.append("It's a draw!")

            # Convert board.svg to board.png
            self.create_board_image(board, human_color, move, from_square)

            # Display background color
            self.screen.fill(self.DARKGRAY)
            # Display board
            board_image = pygame.image.load("board.png")
            self.screen.blit(board_image, (0, 0), pygame.Rect(0, 0, self.board_size, self.board_size))
            # Display chat
            self.screen.fill(self.WHITE, pygame.Rect(self.board_size + self.margin_size, self.margin_size, self.chat_width, self.chat_height))
            self.display_chat()
            pygame.display.flip()
            
            # Set framerate
            self.clock.tick(60)

    def play_puzzle(self, board: chess.Board, uci_moves, theme):
        # Initialize puzzle variables
        from_square = None
        human_color = board.turn
        self.chats.append("You are playing as " + ("White" if human_color == chess.WHITE else "Black"))
        move = chess.Move.null()
        move_num = 0
        start_time = proactive_start = time()
        proactive_timeout = 10
        display_theme = False
        num_mistakes = 0
        q = False

        # Puzzle loop
        running = True
        while running:
            # Make computer move
            if board.turn != human_color:
                move = chess.Move.from_uci(uci_moves[move_num])
                board.push(move)
                move_num += 1
                proactive_start = time()

            # Check if human is stuck
            if time() - proactive_start > proactive_timeout and not display_theme:
                self.chats.append("Look for a " + theme)
                display_theme = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    q = True

                if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                    # Get the mouse position
                    x, y = pygame.mouse.get_pos()
                    
                    # Convert the position to chess coordinates
                    square = None
                    if x > self.margin_size and x < self.margin_size + self.grid_size and \
                        y > self.margin_size and y < self.margin_size + self.grid_size:
                        file = int((x - self.margin_size) // (self.grid_size / 8))
                        rank = int(7 - (y - self.margin_size) // (self.grid_size / 8))
                        square = chess.square(file, rank) if human_color == chess.WHITE else chess.square(7 - file, 7 - rank)
                    
                    # Determine move
                    if square is None:
                        from_square = None
                    elif from_square is None:
                        from_square = square if board.color_at(square) == board.turn else None
                    elif from_square == square:
                        from_square = None
                    else:
                        # Make the move if it's legal
                        try:
                            human_move = board.find_move(from_square, square)
                        except:
                            from_square = square if board.color_at(square) == board.turn else None
                        else:
                            if human_move.uci() == uci_moves[move_num]:
                                move = human_move
                                board.push(move)
                                move_num += 1
                            else:
                                self.chats.append("Wrong move. Try again.")
                                num_mistakes += 1
                                if not display_theme:
                                    self.chats.append("Look for a " + theme)
                                    display_theme = True
                            from_square = None

            # End puzzle
            if move_num == len(uci_moves):
                self.chats.append("Puzzle solved!")
                running = False

            # Convert board.svg to board.png
            self.create_board_image(board, human_color, move, from_square)

            # Display background color
            self.screen.fill(self.DARKGRAY)
            # Display board.png
            board_image = pygame.image.load("board.png")
            self.screen.blit(board_image, (0, 0), pygame.Rect(0, 0, self.board_size, self.board_size))
            # Display chat
            self.screen.fill(self.WHITE, pygame.Rect(self.board_size + self.margin_size, self.margin_size, self.chat_width, self.chat_height))
            self.display_chat()
            pygame.display.flip()

            # Set framerate
            self.clock.tick(60)

        total_time = time() - start_time
        return (total_time, num_mistakes, display_theme, q)

    def play_puzzles(self, puzzles):
        t_tot = m_tot = x_tot = r_tot = 0
        n = len(puzzles)

        for i, puzzle in puzzles.iterrows():
            self.chats.append("Puzzle " + str(i + 1) + " of " + str(n))
            board = chess.Board(puzzle["Board"])
            uci_moves = puzzle["Moves"]
            theme = puzzle["Theme"]
            r = puzzle["Rating"]
            t, m, x, q = self.play_puzzle(board, uci_moves, theme)
            t_tot += t; m_tot += m; x_tot += x; r_tot += r
            if q:
                break
        print("Avg:", t_tot / n, "seconds,", m_tot / n, "mistakes,", x_tot / n, "explanations,", r_tot / n, "rating")

if __name__ == "__main__":
    # Obtain puzzles
    puzzles = pd.read_excel("puzzles.xlsx")
    puzzles["Moves"] = puzzles["Moves"].apply(lambda x: x.split()) # Convert string of moves into list
    
    # Run puzzles in GUI
    puzzles = puzzles.sample(10).reset_index(drop=True)
    gui = Chess_Chat_GUI()
    gui.init()
    gui.play_puzzles(puzzles)
    gui.quit()

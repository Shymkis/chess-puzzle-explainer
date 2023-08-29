import chess
import chess.engine
import chess.svg
import pandas as pd
import pygame as pg
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
        pg.init()
        pg.display.set_icon(pg.image.load("icon.svg"))
        pg.display.set_caption("Chess Chat")
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pg.time.Clock()
        self.font = pg.freetype.SysFont("Arial", 18)
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish_15.1_win_x64_avx2/stockfish-windows-2022-x86-64-avx2.exe")

    def quit(self):
        # Quit pygame
        self.engine.quit()
        pg.quit()

    def get_square(self, x, y):
        # Convert the position to chess coordinates
        square = None
        if x > self.margin_size and x < self.margin_size + self.grid_size and \
            y > self.margin_size and y < self.margin_size + self.grid_size:
            file = int((x - self.margin_size) // (self.grid_size / 8))
            rank = int(7 - (y - self.margin_size) // (self.grid_size / 8))
            square = chess.square(7 - file, 7 - rank) if self.human_color == chess.BLACK else chess.square(file, rank)
        return square

    def get_pieces_captures_and_checks(self, uci_moves):
        pieces = []
        captures = []
        checks = []
        board = self.board.copy()
        for uci_move in uci_moves:
            uci_piece = uci_move[:2]
            pieces.append(board.piece_at(chess.parse_square(uci_piece)))

            uci_capture = uci_move[2:]
            captures.append(board.piece_at(chess.parse_square(uci_capture)))

            board.push(chess.Move.from_uci(uci_move))
            checks.append(board.is_check())
        return pieces, captures, checks

    def create_board_image(self):
        # Get last move, if it exists
        try:
            lastmove = self.board.peek()
        except:
            lastmove = None
        # Convert board.svg to board.png
        drawing = chess.svg.board(
            self.board,
            orientation = chess.WHITE if self.human_color is None else self.human_color,
            lastmove = lastmove,
            check = self.board.king(self.board.turn) if self.board.is_check() else None,
            fill = {self.from_square: "#cc0000cc"},
            size = self.board_size
        )
        f = open("board.svg", 'w')
        f.write(drawing)
        f.close()
        svg2png(url = "board.svg", write_to = "board.png")
        return pg.image.load("board.png")

    def display_chat_messages(self, pad = 6, scroll_up = True, focused = True, caret = True):
        pos = [self.board_size + self.margin_size + pad, self.margin_size]
        if scroll_up:
            pos[1] += self.chat_height
            if caret:
                chat = "|" if pg.time.get_ticks() % 1060 < 530 else " "
                rect = self.font.get_rect("|")
                pos[1] -= rect.height + pad
                self.font.render_to(self.screen, pos, chat, self.BLACK)
            for i, chat in enumerate(self.chats[::-1]):
                col = self.GRAY if focused and i != 0 else self.BLACK
                rect = self.font.get_rect(chat)
                pos[1] -= rect.height + pad
                self.font.render_to(self.screen, pos, chat, col)
        else:
            pos[1] += pad
            for i, chat in enumerate(self.chats):
                col = self.GRAY if focused and i + 1 != len(self.chats) else self.BLACK
                rect = self.font.render_to(self.screen, pos, chat, col)
                pos[1] += rect.height + pad
            if caret:
                chat = "|" if pg.time.get_ticks() % 1060 < 530 else " "
                rect = self.font.get_rect("|")
                self.font.render_to(self.screen, pos, chat, self.BLACK)
                pos[1] += rect.height + pad

    def draw_frame(self, board_image):
            # Display board
            self.screen.blit(board_image, (0, 0), pg.Rect(0, 0, self.board_size, self.board_size))
            # Display chat background
            self.screen.fill(self.WHITE, pg.Rect(self.board_size, 0, self.chatbox_width, self.screen_height))
            # Display chat messages
            self.display_chat_messages()
            # Display chat border
            self.screen.fill(self.DARKGRAY, pg.Rect(self.board_size, 0, self.chatbox_width, self.margin_size)) # top
            self.screen.fill(self.DARKGRAY, pg.Rect(self.board_size, 0, self.margin_size, self.screen_height)) # left
            self.screen.fill(self.DARKGRAY, pg.Rect(self.board_size + self.margin_size + self.chat_width + 1, 0, self.margin_size, self.screen_height)) # right
            self.screen.fill(self.DARKGRAY, pg.Rect(self.board_size, self.margin_size + self.chat_height + 1, self.chatbox_width, self.margin_size)) # bottom
            # Show display
            pg.display.flip()

    def play_game(self, human_color = None):
        # Initialize game variables
        self.board = chess.Board()
        self.human_color = human_color
        if self.human_color is None:
            self.chats.append("CPU vs. CPU game.")
        else:
            self.chats.append("You are playing as " + ("White." if self.human_color == chess.WHITE else "Black."))
        self.from_square = None

        # Game loop
        running = True
        while running:
            # Make computer move
            if self.board.turn != self.human_color:
                move = self.engine.play(self.board, chess.engine.Limit(time = .25)).move
                self.board.push(move)

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                
                if event.type == pg.MOUSEBUTTONDOWN and self.board.turn == self.human_color:
                    # Get the mouse position and corresponding square
                    x, y = pg.mouse.get_pos()
                    square = self.get_square(x, y)
                    
                    # Determine move
                    if square is None:
                        self.from_square = None
                    elif self.from_square is None:
                        self.from_square = square if self.board.color_at(square) == self.human_color else None
                    elif self.from_square == square:
                        self.from_square = None
                    else:
                        # Make the move if it's legal
                        try:
                            move = self.board.find_move(self.from_square, square)
                        except:
                            self.from_square = square if self.board.color_at(square) == self.human_color else None
                        else:
                            self.board.push(move)
                            self.from_square = None
            
            # End game
            if self.board.is_game_over():
                running = False
                result = self.board.result()
                if result == "1-0":
                    self.chats.append("White wins!")
                elif result == "0-1":
                    self.chats.append("Black wins!")
                else:
                    self.chats.append("It's a draw!")

            # Draw the frame
            board_image = self.create_board_image()
            self.draw_frame(board_image)
            
            # Set framerate
            self.clock.tick(60)

    def play_puzzle(self, uci_moves, theme):
        # Initialize puzzle variables
        self.human_color = self.board.turn
        self.chats.append("You are playing as " + ("White." if self.human_color == chess.WHITE else "Black."))
        self.from_square = None
        pieces, captures, checks = self.get_pieces_captures_and_checks(uci_moves)
        move_num = 0
        start_time = proactive_start = time()
        proactive_timeout = 2
        display_theme = display_piece = display_capture = display_check = False
        num_mistakes = 0
        q = False

        # Puzzle loop
        running = True
        while running:
            # Make computer move
            if self.board.turn != self.human_color:
                move = chess.Move.from_uci(uci_moves[move_num])
                self.board.push(move)
                move_num += 1
                proactive_start = time()
                display_piece = display_capture = display_check = False

            # Check if human is stuck
            if time() - proactive_start > proactive_timeout and not display_theme:
                self.chats.append("Look for a " + theme + ".")
                display_theme = True
                proactive_start = time()
            if time() - proactive_start > proactive_timeout and not display_check:
                check = checks[move_num]
                if check:
                    self.chats.append("Look to check their king.")
                    display_check = True
                    proactive_start = time()
            if time() - proactive_start > proactive_timeout and not display_piece:
                piece = pieces[move_num]
                if piece is not None:
                    self.chats.append("Look to move your " + chess.piece_name(piece.piece_type) + ".")
                    display_piece = True
                    proactive_start = time()
            if time() - proactive_start > proactive_timeout and not display_capture:
                capture = captures[move_num]
                if capture is not None:
                    self.chats.append("Look to capture their " + chess.piece_name(capture.piece_type) + ".")
                    display_capture = True
                    proactive_start = time()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    q = True

                if event.type == pg.MOUSEBUTTONDOWN and self.board.turn == self.human_color:
                    # Get the mouse position and corresponding square
                    x, y = pg.mouse.get_pos()
                    square = self.get_square(x, y)
                    
                    # Determine move
                    if square is None:
                        self.from_square = None
                    elif self.from_square is None:
                        self.from_square = square if self.board.color_at(square) == self.human_color else None
                    elif self.from_square == square:
                        self.from_square = None
                    else:
                        # Make the move if it's legal
                        try:
                            human_move = self.board.find_move(self.from_square, square)
                        except:
                            self.from_square = square if self.board.color_at(square) == self.human_color else None
                        else:
                            if human_move.uci() == uci_moves[move_num]:
                                move = human_move
                                self.board.push(move)
                                move_num += 1
                            else:
                                self.chats.append("Wrong move. Try again.")
                                num_mistakes += 1
                                if not display_theme:
                                    self.chats.append("Look for a " + theme + ".")
                                    display_theme = True
                            self.from_square = None

            # End puzzle
            if move_num == len(uci_moves):
                self.chats.append("Puzzle solved!")
                running = False

            # Draw the frame
            board_image = self.create_board_image()
            self.draw_frame(board_image)

            # Set framerate
            self.clock.tick(60)

        total_time = time() - start_time
        return (total_time, num_mistakes, display_theme, q)

    def play_puzzles(self, puzzles):
        t_tot = m_tot = x_tot = r_tot = 0
        n = len(puzzles)

        for i, puzzle in puzzles.iterrows():
            self.chats.append("Puzzle " + str(i + 1) + " of " + str(n) + ".")
            self.board = chess.Board(puzzle["Board"])
            uci_moves = puzzle["Moves"]
            theme = puzzle["Theme"]
            r = puzzle["Rating"]
            t, m, x, q = self.play_puzzle(uci_moves, theme)
            t_tot += t; m_tot += m; x_tot += x; r_tot += r
            if q:
                break
        print("Avg:", t_tot / (i+1), "seconds,", m_tot / (i+1), "mistakes,", x_tot / (i+1), "explanations,", r_tot / (i+1), "rating")

if __name__ == "__main__":
    # Obtain puzzles
    puzzles = pd.read_excel("puzzles.xlsx")
    puzzles["Moves"] = puzzles["Moves"].apply(lambda x: x.split()) # Convert string of moves into list
    # puzzles = puzzles.sample(10).reset_index(drop=True)
    
    # Run puzzles in GUI
    gui = Chess_Chat_GUI()
    gui.init()
    gui.play_puzzles(puzzles)
    gui.quit()

import chess
import chess.engine
import chess.svg
import pandas as pd
import pygame
from cairosvg import svg2png
from time import time

def play_game(human_color = None):
    # Initialize pygame
    pygame.init()

    # Initialize engine
    engine = chess.engine.SimpleEngine.popen_uci("stockfish_15.1_win_x64_avx2/stockfish-windows-2022-x86-64-avx2.exe")

    # Set up the display
    screen_size = 720
    margin_size = 27
    board_size = screen_size - 2*margin_size
    screen = pygame.display.set_mode((screen_size, screen_size))
    clock = pygame.time.Clock()

    # Initialize variables
    board = chess.Board()
    from_square = None
    move = chess.Move.null()

    # Game loop
    running = True
    while running:
        if board.turn != human_color:
            # Make Stockfish move
            move = engine.play(board, chess.engine.Limit(time = .0001)).move
            board.push(move)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                # Get the mouse position
                x, y = pygame.mouse.get_pos()
                
                # Convert the position to chess coordinates
                square = None
                if x > margin_size and x < margin_size + board_size and y > margin_size and y < margin_size + board_size:
                    file = int((x - margin_size) // (board_size / 8))
                    rank = int(7 - (y - margin_size) // (board_size / 8))
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
        
        # Convert board.svg to board.png
        drawing = chess.svg.board(
            board,
            orientation = chess.WHITE if human_color is None else human_color,
            lastmove = move,
            check = board.king(board.turn) if board.is_check() else None,
            fill = {from_square: "#cc0000cc"},
            size = screen_size
        )
        f = open("board.svg", 'w')
        f.write(drawing)
        svg2png(url = "board.svg", write_to = "board.png")
        
        # Display board.png
        board_image = pygame.image.load("board.png")
        screen.blit(board_image, (0, 0))
        pygame.display.flip()
        
        # Set framerate
        clock.tick(60)

    # Quit engine
    engine.quit()

    # Quit pygame
    pygame.quit()

    # Game over
    result = board.result()
    if result == "1-0":
        print("White wins!")
    elif result == "0-1":
        print("Black wins!")
    else:
        print("It's a draw!")

def play_puzzle(board, uci_moves, theme):
    # Initialize pygame
    pygame.init()

    # Set up the display
    screen_size = 720
    margin_size = 27
    board_size = screen_size - 2*margin_size
    screen = pygame.display.set_mode((screen_size, screen_size))
    clock = pygame.time.Clock()

    # Initialize variables
    from_square = None
    human_color = board.turn
    move = chess.Move.null()
    move_num = 0
    start_time = proactive_start = time()
    proactive_timeout = 10
    display_theme = False
    num_mistakes = 0

    # Puzzle loop
    running = True
    while running:
        if board.turn != human_color:
            # Make CPU move
            move = chess.Move.from_uci(uci_moves[move_num])
            board.push(move)
            move_num += 1
            proactive_start = time()
        
        if time() - proactive_start > proactive_timeout and not display_theme:
            print(theme)
            display_theme = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                # Get the mouse position
                x, y = pygame.mouse.get_pos()
                
                # Convert the position to chess coordinates
                square = None
                if x > margin_size and x < margin_size + board_size and y > margin_size and y < margin_size + board_size:
                    file = int((x - margin_size) // (board_size / 8))
                    rank = int(7 - (y - margin_size) // (board_size / 8))
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
                            print("Wrong move. Try again.")
                            num_mistakes += 1
                            if not display_theme:
                                print(theme)
                                display_theme = True
                        from_square = None
        
        # Convert board.svg to board.png
        drawing = chess.svg.board(
            board,
            orientation = human_color,
            lastmove = move,
            check = board.king(board.turn) if board.is_check() else None,
            fill = {from_square: "#cc0000cc"},
            size = screen_size
        )
        f = open("board.svg", 'w')
        f.write(drawing)
        svg2png(url = "board.svg", write_to = "board.png")
        
        # Display board.png
        board_image = pygame.image.load("board.png")
        screen.blit(board_image, (0, 0))
        pygame.display.flip()
        
        # Set framerate
        clock.tick(60)

        # End puzzle
        if move_num == len(uci_moves):
            print("Puzzle solved!")
            running = False

    # Quit pygame
    pygame.quit()

    total_time = time() - start_time
    return (total_time, num_mistakes, display_theme)

# Obtain puzzles
puzzles = pd.read_excel("puzzles.xlsx")
puzzles["Moves"] = puzzles["Moves"].apply(lambda x: x.split()) # Convert string of moves into list

if __name__ == "__main__":
    t_tot = m_tot = x_tot = r_tot = 0
    n = len(puzzles)

    # puzzles = puzzles.sample(n).reset_index(drop=True)
    for _, puzzle in puzzles.iterrows():
        board = chess.Board(puzzle["Board"])
        uci_moves = puzzle["Moves"]
        theme = puzzle["Theme"]
        r = puzzle["Rating"]
        t, m, x = play_puzzle(board, uci_moves, theme)
        t_tot += t; m_tot += m; x_tot += x; r_tot += r
    print("Avg:", t_tot / n, "seconds,", m_tot / n, "mistakes,", x_tot / n, "explanations,", r_tot / n, "rating")

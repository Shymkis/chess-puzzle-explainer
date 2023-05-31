import chess
import chess.svg
import pygame
import random
from cairosvg import svg2png

def play_game(human_color = None):
    # Initialize pygame
    pygame.init()

    # Set up the display
    board_size = 400
    screen = pygame.display.set_mode((board_size, board_size))
    clock = pygame.time.Clock()

    # Initialize variables
    board = chess.Board()
    from_square = None
    move = chess.Move.null()

    # Game loop
    running = True
    while running:
        if board.turn != human_color:
            # Make random CPU move
            move = random.choice(list(board.legal_moves))
            board.push(move)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                # Get the mouse position
                x, y = pygame.mouse.get_pos()
                
                # Convert the position to chess coordinates
                file = x // (board_size // 8)
                rank = 7 - y // (board_size // 8)
                square = chess.square(file, rank) if human_color == chess.WHITE else chess.square(7 - file, 7 - rank)
                
                # Determine move
                if from_square is None and board.color_at(square) == board.turn:
                    from_square = square
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
            fill = {from_square: "#cc0000cc"},
            size = board_size,
            coordinates = False
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

def play_puzzle(board, uci_moves):
    # Initialize pygame
    pygame.init()

    # Set up the display
    board_size = 400
    screen = pygame.display.set_mode((board_size, board_size))
    clock = pygame.time.Clock()

    # Initialize variables
    from_square = None
    human_color = board.turn
    move = chess.Move.null()
    move_num = 0

    # Puzzle loop
    running = True
    while running:
        if board.turn != human_color:
            # Make CPU move
            move = chess.Move.from_uci(uci_moves[move_num])
            board.push(move)
            move_num += 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and board.turn == human_color:
                # Get the mouse position
                x, y = pygame.mouse.get_pos()
                
                # Convert the position to chess coordinates
                file = x // (board_size // 8)
                rank = 7 - y // (board_size // 8)
                square = chess.square(file, rank) if human_color == chess.WHITE else chess.square(7 - file, 7 - rank)
                
                # Determine move
                if from_square is None and board.color_at(square) == board.turn:
                    from_square = square
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
                        from_square = None
        
        # Convert board.svg to board.png
        drawing = chess.svg.board(
            board,
            orientation = human_color,
            lastmove = move,
            fill = {from_square: "#cc0000cc"},
            size = board_size,
            coordinates = False
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

puzzles = [
    # Fork
    ("8/r1k2pp1/B7/PP6/8/5KP1/8/8 w",["b5b6","c7b8","b6a7"]), # 682
    ("8/2r3pp/4kp2/1RP1p3/1P2b1P1/4N3/5P1P/5K2 b",["e4d3","f1e1","d3b5"]), # 809
    ("8/4k3/B5p1/2p1Pp1p/2P2P1P/3K4/2n5/8 b",["c2b4","d3e3","b4a6"]), # 817
    ("5rk1/p4p2/2pr4/3Pq1p1/2K1P3/2P1QPR1/2P5/8 w",["g3g5","e5g5","e3g5"]), # 1066
    ("8/p2pkpp1/8/4P2p/P3BP2/1Pr1n1P1/1R5P/6K1 b",["c3c1","g1f2","e3d1","f2e2","d1b2"]), # 1076
    ("2kr3r/pppq4/4bp2/2Pp1n2/3B3p/1P5P/P2QB1P1/R3RKN1 b",["f5g3","f1f2","g3e4","f2e3","e4d2"]), # 1462
    ("3q2k1/5p1p/p1Bpr1p1/2n1p1P1/1pP4Q/PPn5/3RPP1P/2R3K1 b",["c5b3","a3b4","b3c1"]), # 1902
    # Mate in 1
    ("r3kb1B/ppp1n2p/2n3p1/1B1p2q1/8/1P2PP1b/P1PPQP1K/RN2R3 b",["g5g2"]), # 802
    ("k3r3/p5Q1/8/2B1n1p1/2P5/5P2/Pq1r2PP/4RK2 w",["g7a7"]), # 843
    ("8/8/R6P/5p2/p7/4k1P1/r7/4K3 b",["a2a1"]), # 1170
    ("r3r2Q/2pb1k2/1p1p2p1/p1nP1pq1/2P1P3/2N5/PP6/1K1R1B1R w",["h1h7"]), # 1397
    ("3R4/5p2/4kNp1/4P2p/4KP2/6P1/7r/4n3 w",["d8e8"]), # 1503
    ("r1r5/2R1R2p/2p2k2/2p2Pp1/6P1/p5P1/P4P2/6P1 w",["e7e6"]), # 1763
    ("4k3/4r3/p6p/P2Q2p1/3N1p2/5K1P/1R4P1/4q3 b",["e1g3"]), # 1997
    # Pin
    ("r3k2r/p1pq1pb1/1p1p3p/3P2pP/4P3/8/P3BPP1/1R1QK2R w",["e2b5","d7b5","b1b5"]), # 896
    ("8/3r4/6kP/3r4/5P1Q/8/6PK/8 b",["d5h5","h4h5","g6h5"]), # 1006
    ("rn5k/pp4pp/2pp4/q4r2/2P5/2N1Q2P/PP3PP1/R3K2R b",["f5e5","e1g1","e5e3"]), # 1039
    ("8/pp3rkp/2p1rb2/2P5/5PP1/1P1RB2P/P5B1/6K1 b",["e6e3","d3e3","f6d4"]), # 1210
    ("4r1k1/pp3p2/2pp1qp1/8/3QPP1p/bP4P1/P3N2P/3R1BK1 b",["a3c5","d4c5","d6c5"]), # 1222
    ("2r1r1k1/pp2p2p/3qbbp1/2pp1p2/3P1P1P/PBP2QP1/1PKN4/3RR3 w",["e1e6","d6e6","b3d5","e6d5","f3d5"]), # 1525
    ("4r2k/3b3r/p2B2R1/1p1B4/2p5/8/P1p3PP/6K1 w",["d6e5","h7g7","g6h6"]), # 1916
]

if __name__ == "__main__":
    play_game()
    # for puzzle in puzzles:
    #     board = chess.Board(puzzle[0])
    #     uci_moves = puzzle[1]
    #     play_puzzle(board, uci_moves)
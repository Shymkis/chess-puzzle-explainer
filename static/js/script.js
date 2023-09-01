// NOTE: this example uses the chess.js library:
// https://github.com/jhlywa/chess.js
function onDragStart(source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // do not pick up pieces if it's not the player's turn
  if (game.turn() != player_color) return false

  // only pick up pieces for player color
  if (!piece.startsWith(player_color)) return false
}

function makeRandomMove() {
  let possibleMoves = game.moves()
  console.log(possibleMoves)

  // game over
  if (possibleMoves.length === 0) return

  let randomIdx = Math.floor(Math.random() * possibleMoves.length)
  game.move(possibleMoves[randomIdx])
  board.position(game.fen())
}

function makePuzzleMove() {
  game.move(moves[move_num], { sloppy: true })
  board.position(game.fen())
  move_num++
}

function onDrop(source, target) {
  // see if the move is legal
  let move = game.move({
    from: source,
    to: target,
    promotion: 'q' // NOTE: always promote to a queen for example simplicity
  })

  // illegal move
  if (move === null) return 'snapback'

  // wrong move
  if (move.from + move.to != moves[move_num]) {
    game.undo()
    return 'snapback'
  }

  // correct move
  move_num++
  completed = (move_num == moves.length)

  // make next puzzle move
  if (!completed) window.setTimeout(makePuzzleMove, 250)
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd() {
  board.position(game.fen())

  if (completed) {
    puzzle_num++
    nextPuzzle()
  }
}

function nextPuzzle() {
  if (puzzle_num == puzzles.length) return

  fen = puzzles[puzzle_num]["Board"]
  moves = puzzles[puzzle_num]["Moves"].split(" ")
  theme = puzzles[puzzle_num]["Theme"]
  rating = puzzles[puzzle_num]["Rating"]
  
  game = new Chess(fen)
  player_color = game.turn()
  move_num = 0
  completed = false
  
  let config = {
    draggable: true,
    position: fen,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    orientation: (player_color == 'w') ? "white" : "black"
  }
  board = Chessboard('board', config)
}

const res = await fetch('./static/puzzles.json')
let puzzles = await res.json()
console.log(puzzles)
let puzzle_num = 0

let board, completed, fen, game, move_num, moves, player_color, rating, theme

nextPuzzle()

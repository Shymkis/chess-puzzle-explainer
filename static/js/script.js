function onDragStart(source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // do not pick up pieces if it's not the player's turn
  if (game.turn() != player_c) return false

  // only pick up pieces for player color
  if (!piece.startsWith(player_c)) return false
}

function makeRandomMove() {
  let possibleMoves = game.moves()

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

function scrollChat() {
  let scroll_height = 0
  chat_display.children().each(function() { scroll_height += $(this).height() })
  chat_display.animate({ scrollTop: scroll_height })
}

function offerHelp() {
  if (protocol == "no-exp") return

  let last_message = chat_display.find("p").last()
  if (move_num == 0) {
    last_message.after(`<p>Wrong move. Try looking for a <b>` + theme + `</b>.</p>`)
  } else if (move_num == 2) {
    last_message.after(`<p>Wrong move. Finish the ` + theme + ` by <b>capturing</b> the opponent's piece.</p>`)
  }
  let t = chat_display.find(".time").last()
  t.text(new Date().toLocaleTimeString([], { timeStyle: "short" }) + ` | Puzzle ` + (puzzle_num + 1))
  scrollChat()
}

function onDrop(source, target) {
  // see if the move is legal
  let move = game.move({
    from: source,
    to: target,
    promotion: 'q' // NOTE: always promote to a queen for example simplicity
  })

  // illegal move
  if (move === null) return "snapback"

  // wrong move
  if (move.from + move.to != moves[move_num]) {
    game.undo()
    failure = true
    num_mistakes++
    offerHelp()
    return "snapback"
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
    if (!failure) successes++
    puzzle_num++
    nextPuzzle()
  }
}

function nextPuzzle() {
  if (puzzle_num == puzzles.length) {
    let summary_data = {
      "user_id": Math.floor(Math.random() * 1000000),
      "protocol": protocol,
      "mistakes": num_mistakes,
      "mistakes/puzzle": num_mistakes/puzzle_num,
      "successes": successes,
      "successes/puzzle": successes/puzzle_num,
      "seconds": time_limit - timer.remaining,
      "seconds/puzzle": (time_limit - timer.remaining)/puzzle_num
    }
    console.log(summary_data)
    return
  }

  fen = puzzles[puzzle_num]["Board"]
  moves = puzzles[puzzle_num]["Moves"]
  theme = puzzles[puzzle_num]["Theme"]
  rating = puzzles[puzzle_num]["Rating"]
  
  game = new Chess(fen)
  player_c = game.turn()
  player_color = (player_c == 'w') ? "white" : "black"
  move_num = 0, completed = false, failure = false
  
  chat_display.append(`
    <div class="received-msg">
      <p>You are playing the ` + player_color + ` pieces.</p>
      <span class="time">` + new Date().toLocaleTimeString([], { timeStyle: "short" }) + ` | Puzzle ` + (puzzle_num + 1) + `</span>
    </div>
  `)
  scrollChat()

  let config = {
    draggable: true,
    position: fen,
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    orientation: player_color
  }
  board = Chessboard("board", config)
}

function formatTime(minutes, seconds) {
  minutes = minutes < 10 ? "0" + minutes : minutes
  seconds = seconds < 10 ? "0" + seconds : seconds
  timer_display.text(minutes + ':' + seconds)
}

const res = await fetch("./static/data/training-puzzles.json")
let puzzles = await res.json()
let puzzle_num = 0, num_mistakes = 0, successes = 0, failure = false

let protocol = "no-exp"
let chat_display = $("#chat")

let timer_display = $("#timer")
let time_limit = 60*10
let timer = new CountDownTimer(time_limit)
timer.onTick(formatTime)

let board, completed, fen, game, move_num, moves, player_c, player_color, rating, theme

chat_display.append(`
<div class="received-msg">
  <p>Hello! I am your AI teammate. I'm here to assist you with these chess puzzles.</p>
  <span class="time">` + new Date().toLocaleTimeString([], { timeStyle: "short" }) + `</span>
</div>
`)

nextPuzzle()
timer.start()

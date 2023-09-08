function onDragStart(source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // do not pick up pieces if it's not the player's turn
  if (game.turn() != player_c) return false

  // only pick up pieces for player color
  if (!piece.startsWith(player_c)) return false
}

function makePuzzleMove() {
  game.move(moves[move_num], { sloppy: true })
  board.position(game.fen())
  move_num++
  move_start = Date.now()
}

function scrollChat() {
  let scroll_height = 0
  chat_display.children().each(function() { scroll_height += $(this).height() })
  chat_display.animate({ scrollTop: scroll_height })
}

function explain() {
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

  // log legal move
  let move_string = move.from + move.to
  let correct = move_string == moves[move_num]
  let move_end = Date.now()
  $.ajax({
    url: "/user_move",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      "user_id": user_id,
      "puzzle_id": puzzles[puzzle_num]["id"],
      "move_num": move_num + 1,
      "move": move_string,
      "move_start": move_start,
      "move_end": move_end,
      "duration": move_end - move_start,
      "mistake": !correct,
      "protocol": protocol,
    }),
    error: function(error) {
      console.log(error)
    }
  })

  // wrong move
  if (!correct) {
    game.undo()
    if (protocol != "base" && protocol != "testing") explain()
    move_start = Date.now()
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
    puzzle_num++
    nextPuzzle()
  }
}

function nextPuzzle() {
  if (puzzle_num == puzzles.length) {
    console.log("Go to next page")
    return
  }

  fen = puzzles[puzzle_num]["fen"]
  moves = puzzles[puzzle_num]["moves"].split(" ")
  theme = puzzles[puzzle_num]["theme"]
  rating = puzzles[puzzle_num]["rating"]
  
  game = new Chess(fen)
  player_c = game.turn()
  player_color = (player_c == 'w') ? "white" : "black"
  move_num = 0, completed = false
  
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
  move_start = Date.now()
}

function formatTime(minutes, seconds) {
  minutes = minutes < 10 ? "0" + minutes : minutes
  seconds = seconds < 10 ? "0" + seconds : seconds
  timer_display.text(minutes + ':' + seconds)
}

function timesUp() {
  if (this.expired()) {
    console.log("Go to next page")
  }
}

let puzzle_num = 0

let chat_display = $("#chat")

let timer_display = $("#timer")
let time_limit = 60*10
let timer = new CountDownTimer(time_limit)
timer.onTick(formatTime).onTick(timesUp)

let user_id = Math.floor(Math.random()*1000000)

let board, completed, fen, game, move_num, move_start, moves, player_c, player_color, rating, theme

chat_display.append(`
  <div class="received-msg">
    <p>Hello! I am your AI teammate. I'm here to assist you with these chess puzzles.</p>
    <span class="time">` + new Date().toLocaleTimeString([], { timeStyle: "short" }) + `</span>
  </div>
`)

nextPuzzle()
timer.start()

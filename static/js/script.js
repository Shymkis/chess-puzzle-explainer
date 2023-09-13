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
  let move_end = Date.now()
  let move_string = move.from + move.to
  let mistake = move_string != moves[move_num]
  let move_data = JSON.stringify({
    user_id: user_id,
    puzzle_id: puzzles[puzzle_num]["id"],
    move_num: move_num,
    move: move_string,
    start_time: move_start,
    end_time: move_end,
    duration: move_end - move_start,
    mistake: mistake,
    protocol: protocol
  })
  $.ajax({
    url: "/user_move",
    type: "POST",
    contentType: "application/json",
    data: move_data,
    success: function(data) {
      // wrong move
      if (mistake) {
        num_mistakes++
        game.undo()
        if (section == "practice" && protocol != "n") explain()
        move_start = Date.now()
        return "snapback"
      }
      // correct move
      move_num++
      completed = (move_num == moves.length)
      // make next puzzle move
      if (!completed) setTimeout(makePuzzleMove, 250)
    },
    error: function(err) {
      console.log(err)
    }
  })
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd() {
  board.position(game.fen())

  if (completed) {
    let last_message = chat_display.find("p").last()
    last_message.after(`<p>Puzzle ` + (puzzle_num + 1) + ` completed!</p>`)
    let t = chat_display.find(".time").last()
    t.text(new Date().toLocaleTimeString([], { timeStyle: "short" }) + ` | Puzzle ` + (puzzle_num + 1))
    scrollChat()
    
    if (num_mistakes == 0) successes++
    puzzle_num++
    setTimeout(nextPuzzle, 500)
  }
}

function nextSection() {
  // log section
  let section_end = Date.now()
  let section_data = JSON.stringify({
    user_id: user_id,
    section: section,
    start_time: section_start,
    end_time: section_end,
    duration: section_end - section_start,
    successes: successes,
    puzzles: puzzle_num,
    protocol: protocol
  })
  $.ajax({
    url: "/user_section",
    type: "POST",
    contentType: "application/json",
    data: section_data,
    success: function(data) {
      section == "testing" ? location.replace("/survey") : location.replace("/testing")
    },
    error: function(err) {
      console.log(err)
    }
  })
}

function nextPuzzle() {
  if (puzzle_num == puzzles.length) {
    nextSection()
    return
  }

  fen = puzzles[puzzle_num]["fen"]
  moves = puzzles[puzzle_num]["moves"].split(" ")
  theme = puzzles[puzzle_num]["theme"]
  rating = puzzles[puzzle_num]["rating"]
  
  game = new Chess(fen)
  player_c = game.turn()
  player_color = player_c == 'w' ? "white" : "black"
  move_num = 0, num_mistakes = 0, completed = false
  if (puzzle_num == 0) section_start = Date.now()
  
  chat_display.append(`
    <div class="received-msg">
      <p>Puzzle ` + (puzzle_num + 1) + ` of ` + puzzles.length + `.</p>
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
    nextSection()
  }
}

let user_id = Math.floor(Math.random()*1000000)

let puzzle_num = 0, successes = 0

let chat_display = $("#chat")

let timer_display = $("#timer")
let time_limit = 60*.1
let timer = new CountDownTimer(time_limit)
timer.onTick(formatTime).onTick(timesUp)

let board, completed, fen, game, move_num, move_start, moves, num_mistakes, player_c, player_color, puzzles, rating, section_start, theme

$.ajax({
  method: "POST",
  url: "/get_puzzles/" + section,
  dataType: "json",
  success: function(data) {
    puzzles = data
    if (section == "testing") {
      timer_display.parent().prepend("Testing time remaining: ")
      chat_display.append(`
        <div class="received-msg">
          <p>Test your skills on these new puzzles without my help.</p>
          <span class="time">` + new Date().toLocaleTimeString([], { timeStyle: "short" }) + `</span>
        </div>
      `)
    } else {
      timer_display.parent().prepend("Practice time remaining: ")
      chat_display.append(`
        <div class="received-msg">
          <p>Hello! I am your AI teammate. I'm here to assist you with these chess puzzles.</p>
          <span class="time">` + new Date().toLocaleTimeString([], { timeStyle: "short" }) + `</span>
        </div>
      `)
    }
    
    nextPuzzle()
    timer.start()
  },
  error: function(err) {
    console.log(err)
  }
})

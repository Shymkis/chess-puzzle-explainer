import sqlite3
from flask import Flask, g, render_template, request, jsonify
from random import choice, randint

DATABASE = "./static/data/database.db"
PROTOCOLS = ["none", "base", "detail", "foil"]

app = Flask(__name__)

def make_dicts(cursor, row):
    return {cursor.description[i][0]: v for i, v in enumerate(row)}

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    protocol = choice(PROTOCOLS)
    return render_template("index.html", protocol=protocol)

@app.route("/<protocol>")
def chess(protocol):
    if protocol not in PROTOCOLS + ["testing"]: return
    section = "testing" if protocol == "testing" else "practice"
    puzzles = query_db("SELECT id, fen, num_moves, theme, section FROM puzzles WHERE section = ?", [section])
    return render_template("chess.html", puzzles=puzzles, protocol=protocol)

@app.route("/user_move", methods=["POST"])
def user_move():
    data = request.get_json() # retrieve data from JavaScript
    user_id = 100
    con = get_db()
    moves = query_db("SELECT moves FROM puzzles WHERE id = ?", [data["puzzle_id"]], one=True)["moves"].split()
    mistake = moves[data["move_num"]] != data["move"]
    next_move = None if data["move_num"] + 1 == len(moves) else moves[data["move_num"] + 1]
    con.execute(
        "INSERT INTO user_moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [user_id, data["puzzle_id"], data["move_num"],
         data["move"], data["move_start"], data["move_end"],
         data["duration"], mistake, data["protocol"]]
    )
    con.commit()
    con.close()
    return jsonify({"correct": not mistake, "next_move": next_move}) # return data to JavaScript

if __name__ == "__main__":
    app.run(debug=True)

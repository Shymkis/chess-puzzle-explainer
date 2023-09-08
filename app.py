import sqlite3
from flask import Flask, g, render_template, request
from random import choice

DATABASE = "./static/data/database.db"
PROTOCOLS = ["base", "detail", "foil"]

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
    puzzle_type = "testing" if protocol == "testing" else "practice"
    puzzles = query_db("SELECT * FROM puzzles WHERE type = '" + puzzle_type + "'")
    return render_template("chess.html", puzzles=puzzles, protocol=protocol)

@app.route("/user_move", methods=["POST"])
def user_move():
    data = request.get_json() # retrieve data from JavaScript
    con = get_db()
    con.execute(
        "INSERT INTO user_moves VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (data["user_id"], data["unix_time"],
         data["puzzle_id"], data["move_num"],
         data["protocol"], data["move"],
         data["mistake"], data["duration"])
    )
    con.commit()
    con.close()
    return "Success" # return success to JavaScript

if __name__ == "__main__":
    app.run(debug=True)

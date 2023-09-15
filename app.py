import sqlite3
from flask import Flask, g, render_template, request, jsonify
from random import choice

DATABASE = "./static/data/database.db"
PROTOCOLS = [
    'n',    # none
    'p',    # placebic
    'a'     # actionable
]
SECTIONS = ["practice", "testing"]

app = Flask(__name__)

def make_dicts(cursor, row):
    return {cursor.description[i][0]: v for i, v in enumerate(row)}

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False, con=None):
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

@app.route("/practice/<protocol>")
def practice(protocol):
    if protocol not in PROTOCOLS: return
    return render_template("chess.html", section="practice", protocol=protocol)

@app.route("/testing")
def testing():
    return render_template("chess.html", section="testing", protocol='n')

@app.route("/get_puzzles", methods=["POST"])
def get_puzzles():
    section = request.get_json()
    if section not in SECTIONS: return
    puzzles = query_db("SELECT * FROM puzzles WHERE section = ? ORDER BY LENGTH(fen)", [section])
    return jsonify(puzzles)

@app.route("/user_move", methods=["POST"])
def user_move():
    data = request.get_json()
    explanation = query_db(
        "SELECT reason FROM explanations WHERE puzzle_id = ? AND move_num = ? AND protocol = ? AND move = ?",
        [data["puzzle_id"], data["move_num"], data["protocol"], data["move"]],
        one=True
    )
    con = get_db()
    con.execute(
        "INSERT INTO user_moves VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [data["user_id"], data["puzzle_id"], data["move_num"],
         data["section"], data["protocol"], data["move"],
         data["move_start"], data["move_end"], data["move_duration"], data["mistake"]]
    )
    con.execute(
        "REPLACE INTO user_sections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [data["user_id"], data["section"], data["protocol"],
         data["section_start"], data["section_end"], data["section_duration"],
         data["num_moves"], data["successes"], data["puzzles"]]
    )
    con.commit()
    con.close()
    return jsonify(explanation)

if __name__ == "__main__":
    app.run(debug=True)

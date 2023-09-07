import sqlite3
from flask import Flask, g, render_template, request

DATABASE = "./static/data/database.db"

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
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    puzzles = query_db('select * from puzzles')
    return render_template("index.html", puzzles=puzzles)

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json() # retrieve the data sent from JavaScript
    con = get_db()
    con.execute(
        "INSERT INTO performances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data["user_id"], data["date"], data["protocol"],
         data["mistakes"], data["avg_mistakes"],
         data["successes"], data["avg_successes"],
         data["seconds"], data["avg_seconds"])
    )
    con.commit()
    con.close()
    return "Success" # return the result to JavaScript

if __name__ == "__main__":
    app.run(debug=True)

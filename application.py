from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import datetime
from helpers import *
import locale
from re import sub
from decimal import Decimal
import random
from jinja2 import Environment, PackageLoader

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///trivia.db")

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # ensure username was submitted
        if not request.form.get("username"):
            return redirect(url_for("login_error"))
        # ensure password was submitted
        elif not request.form.get("password"):
            return redirect(url_for("login_error"))
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return ("username does not exist")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

                # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation")
        elif request.form.get("confirmation")!=request.form.get("password"):
                return apology("passwords don't match up")
        # check to see whether username already exists
        elif len(db.execute("SELECT id FROM users WHERE username = :usr;", usr=request.form.get("username"))):
                return apology("username already exists")
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) == 1:
            return apology("username already taken")
        insert = db.execute("INSERT INTO users (username,hash) VALUES (:username,:hash1)", username=request.form.get("username"),hash1=pwd_context.hash(request.form.get("password")))
        return redirect(url_for("login"))
    else:
        return render_template("register.html")

score = 0
game_id = 1

@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    # maak variabelen aan
    global score
    global game_id
    game = ast.literal_eval(db.execute("SELECT questions FROM games WHERE game_id = :game_id", game_id=game_id)[0]["questions"])["results"][score]

    # haal de vragen en antwoorden op voor de huidige game
    if request.method == "GET":
        question = game["question"]
        answers = [game["correct_answer"], game["incorrect_answers"][0], game["incorrect_answers"][1], game["incorrect_answers"][2]]
        random.shuffle(answers)
        return render_template("play.html", question=question, answers=answers)
    else:
    # als de gebruiker het goede antwoord geeft, verhoog de score
        if request.form.get("answer") == game["correct_answer"]:
            score += 1
            return redirect(url_for('play'))
        else:
            # als de gebruiker de vraag fout heeft, kijk of hij de eerste/tweede is die speelt
            to_beat = db.execute("SELECT score FROM games WHERE game_id = :game_id", game_id=game_id)[0]["score"]
            if not to_beat:
                # als de gebruiker de eerste is die speelt, sla zijn score op
                db.execute("UPDATE games SET score = :score WHERE game_id = :game_id", score=score, game_id=game_id)[0]["score"]
                score = 0
                return "jammer pik"
            else:
                # kijk of de gebruiker gewonnen/verloren/gelijk gespeeld heeft
                if to_beat > score:
                    score = 0
                    return "verloren"
                elif to_beat < score:
                    score = 0
                    return "gewonnen"
                elif to_beat == score:
                    score = 0
                    return "gelijkspel"
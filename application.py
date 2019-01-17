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
            return render_template("login.error.html")
        # ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.error.html")
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return render_template("login.error.html")

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
        invalid = "!@#$%^&*()~`=+/?><.,;:{}\[]|"
        # check for invlaid characters
        for char in request.form.get("username"):
            if char in invalid:
                return render_template("register.error.html")
        if not request.form.get("username"):
            return render_template("register.error.html")
        elif not request.form.get("password"):
            return render_template("register.error.html")
        elif not request.form.get("confirmation"):
            return render_template("register.error.html")
        elif request.form.get("confirmation")!=request.form.get("password"):
            return render_template("register.error.html")
        # check to see whether username already exists
        elif len(db.execute("SELECT id FROM users WHERE username = :usr;", usr=request.form.get("username"))):
            return render_template("register.error.html")
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # check if username is taken
        if len(rows) == 1:
            return render_template("register.error.html")
        # add user to database
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

@app.route("/find_game", methods=["GET", "POST"])
@login_required
def find_game():
    # maak variabele aan
    global game_id

    if request.method == "GET":
        return render_template("find_game.html")
    else:
        # als de gebruiker een username heeft gezocht, zoek deze op in de database
        if request.form['find_button'] == 'search':
            username = request.form.get("user")
            results = db.execute("SELECT id FROM users WHERE username = :username", username=username)
            # als de username bestaat, maak een variabele aan en kijk of deze niet hetzelfde is als de huidige user
            if results:
                invite_id = results[0]["id"]
                if invite_id == session.get("user_id"):
                    return "je kan jezelf niet uitdagen"
                else:
                    # maak een game aan met de twee id's en vind de nieuwe game id
                    create_game(session.get("user_id"), invite_id)
                    game_id = db.execute("SELECT max(game_id) FROM games WHERE player1_id = :user_id AND player2_id = :invite_id", user_id=session.get("user_id"), invite_id=invite_id)[0]["max(game_id)"]
                    # plaats de speler in-game
                    return redirect(url_for("play"))
            else:
                return "username does not exist"
        # als de gebruiker een random opponent kiest, haal alle ids uit de database
        elif request.form['find_button'] == 'random':
            ids = db.execute("SELECT id FROM users")
            random_id = random.randrange(len(ids))
            invite_id = ids[random_id]["id"]
            # blijf een random id kiezen tot het een andere is dan die van de huidige user
            while invite_id == session.get("user_id"):
                random_id = random.randrange(len(ids))
                invite_id = ids[random_id]["id"]
            # maak een game aan met de twee id's en vind de nieuwe game id
            create_game(session.get("user_id"), invite_id)
            game_id = db.execute("SELECT max(game_id) FROM games WHERE player1_id = :user_id AND player2_id = :invite_id", user_id=session.get("user_id"), invite_id=invite_id)[0]["max(game_id)"]
            # plaats de speler in-game
            return redirect(url_for("play"))

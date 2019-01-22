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

# declare variables
score = 0
game_id = 0
results = []


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global game_id
    global score
    score = 0
    if request.method == "GET":
        # find users' current games
        rows = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player1_id = :id and status = :active",
                          id=session["user_id"], active=("active"))
        rows2 = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player2_id = :id and status = :active",
                           id=session["user_id"], active=("active"))
        if rows or rows2:
            return render_template("index.html", current=rows, current2=rows2)
        else:
            return render_template("index.html")
    else:
        # find on which game the user clicked and send them to that game
        game_id = int(request.form.get("game_id"))
        return redirect(url_for("play"))


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
        # test user input
        if not request.form.get("username"):
            return render_template("register.error.html")
        elif not request.form.get("password"):
            return render_template("register.error.html")
        elif not request.form.get("confirmation"):
            return render_template("register.error.html")
        elif request.form.get("confirmation") != request.form.get("password"):
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
        insert = db.execute("INSERT INTO users (username,hash) VALUES (:username,:hash1)",
                            username=request.form.get("username"), hash1=pwd_context.hash(request.form.get("password")))
        return redirect(url_for("login"))
    else:
        return render_template("register.html")


@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    """Page where users can answers questions."""
    # initiate game
    global score
    global game_id
    if game_id > 0:
        game = ast.literal_eval(db.execute("SELECT questions FROM games WHERE game_id = :game_id",
                                           game_id=game_id)[0]["questions"])["results"][score]
        players = db.execute("SELECT player1_id, player2_id FROM games WHERE game_id = :game_id", game_id=game_id)
        to_beat = db.execute("SELECT score FROM games WHERE game_id = :game_id", game_id=game_id)[0]["score"]
    else:
        return "No game found"
    # find questions and answers of current game
    if request.method == "GET":
        question = game["question"]
        answers = [game["correct_answer"], game["incorrect_answers"][0], game["incorrect_answers"][1], game["incorrect_answers"][2]]
        random.shuffle(answers)
        # check against who the player is playing
        if session.get("user_id") == players[0]["player1_id"]:
            opponent = db.execute("SELECT username FROM users WHERE id = :other_id",
                                  other_id=players[0]["player2_id"])[0]["username"]
        elif session.get("user_id") == players[0]["player2_id"]:
            opponent = db.execute("SELECT username FROM users WHERE id = :other_id",
                                  other_id=players[0]["player1_id"])[0]["username"]
        return render_template("play.html", question=question, answers=answers, to_beat=to_beat, opponent=opponent, score=score)
    else:
        # if the user answered all questions correct, end their turn
        if score >= 50:
            db.execute("UPDATE games SET score = :score, status = :status WHERE game_id = :game_id",
                       score=score, game_id=game_id, status="active")
            score = 0
            return "Alle vragen goed"
        else:
            # increase the score when the user gives the right answer
            if request.form.get("answer") == game["correct_answer"]:
                score += 1
                return redirect(url_for('play'))
            else:
                # when the user doesn't give the right answer, check who is playing (player 1 or player 2)
                if to_beat == 999:
                    # if player 1 is playing, save their score
                    db.execute("UPDATE games SET score = :score, status = :status WHERE game_id = :game_id",
                               score=score, game_id=game_id, status="active")
                    score = 0
                    game_id = 0
                    return "jammer pik"
                else:
                    # if player 2 is playing, check who won
                    if to_beat > score:
                        winner = find_username(players[0]["player1_id"])
                        loser = find_username(session.get("user_id"))
                        result = winner + " " + str(to_beat) + "-" + str(score) + " " + loser
                        finish_game(result, game_id)
                        score = 0
                        game_id = 0
                        return "verloren"
                    elif to_beat < score:
                        winner = find_username(session.get("user_id"))
                        loser = find_username(players[0]["player1_id"])
                        result = loser + " " + str(to_beat) + "-" + str(score) + " " + winner
                        finish_game(result, game_id)
                        score = 0
                        game_id = 0
                        return "gewonnen"
                    elif to_beat == score:
                        score = 0
                        db.execute("UPDATE games SET status = :status WHERE game_id = :game_id", status="draw", game_id=game_id)
                        game_id = 0
                        return "gelijkspel"


@app.route("/find_game", methods=["GET", "POST"])
@login_required
def find_game():
    """Allow the user to search for opponents"""
    # create variables
    global game_id
    global results
    global score
    score = 0
    if request.method == "GET":
        return render_template("find_game.html")
    else:
        # if the user typed in a username, look it up in the database
        if request.form['find_button'] == 'search':
            username = request.form.get("user")
            results = db.execute(
                "SELECT id, username FROM users WHERE username LIKE :username COLLATE NOCASE LIMIT 10", username=username+"%")
            # if the username exists, save it and show the user the results
            return redirect(url_for("browse_users"))
        # if the user chooses a random user, get all id's from the databse
        elif request.form['find_button'] == 'random':
            ids = db.execute("SELECT id FROM users")
            # choose a random id
            random_id = random.randrange(len(ids))
            invite_id = ids[random_id]["id"]
            # keep choosing a random id while the random id is the same as the user's id
            while invite_id == session.get("user_id"):
                random_id = random.randrange(len(ids))
                invite_id = ids[random_id]["id"]
            # create a game with the user id and the random id and look up the game id
            game_id = create_game(session.get("user_id"), invite_id)
            # put the player in-game
            return redirect(url_for("play"))


@app.route("/browse_users", methods=["GET", "POST"])
@login_required
def browse_users():
    """Show the user all matching users and let them invite them."""
    global results
    global game_id
    if request.method == "POST":
        # find which user was invited
        invite_id = int(request.form.get("invite_id"))
        # check input
        if invite_id == session.get("user_id"):
            return "je kan jezelf niet uitdagen"
        else:
            # create a game and lookup the game id
            game_id = create_game(session.get("user_id"), invite_id)
            # put the player in-game
            return redirect(url_for("play"))
    else:
        return render_template("browse_users.html", results=results)


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Shows the user their match history."""
    global score
    score = 0
    # find all the users' games that are done
    history = db.execute("SELECT game_id, status FROM games WHERE (status != :active AND status != :starting) AND (player1_id = :user_id OR player2_id = :user_id) LIMIT 10",
                         active="active", starting="starting", user_id=session.get("user_id"))
    # find the usernames of the players involved in the matches
    for game in range(len(history)):
        matchup = db.execute("SELECT player1_name, player2_name FROM games WHERE game_id = :game_id",
                             game_id=history[game]["game_id"])
        history[game]["matchup"] = matchup[0]["player1_name"] + " vs. " + matchup[0]["player2_name"]
    return render_template("history.html", history=history)
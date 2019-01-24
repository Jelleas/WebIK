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
finished = 0
results = []


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global game_id
    global score
    # finished == 1 means wrong answer, 2 means lost, 3 means won, 4 means draw, 5 means all answers correct
    global finished
    score = 0
    if request.method == "GET":
        # find users' current games
        user_index = index_info(session.get("user_id"))
        rows = user_index[0]
        rows2 = user_index[1]
        # if the user has active games, show them
        if rows or rows2:
            return render_template("index.html", current=rows, current2=rows2, finished=finished)
        else:
            return render_template("index.html", finished=finished)
    else:
        # find on which game the user clicked and send them to that game
        tried_id = int(request.form.get("game_id"))
        # make sure the user hasn't altered game_ids
        if has_access(tried_id, session.get("user_id")):
            game_id = tried_id
            return redirect(url_for("play"))
        else:
            return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    global finished
    finished = 0
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
        rows = find_rows(request.form.get("username"))

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
        elif len(check_exists(request.form.get("username"))):
            return render_template("register.error.html")
        # query database for username
        rows = find_rows(request.form.get("username"))
        games_won = 0

        # check if username is taken
        if len(rows) == 1:
            return render_template("register.error.html")
        # add user to database
        create_user(request.form.get("username"), pwd_context.hash(request.form.get("password")), games_won,request.form.get("mail"))
        return redirect(url_for("login"))
    else:
        return render_template("register.html")


@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    """Page where users can answers questions."""
    # initialize game
    global score
    global game_id
    global finished
    # make sure the user is joining a valid game
    if game_id > 0:
        thisRound = init_game(game_id)
        if thisRound:
            game = thisRound[0]["results"][score]
            players = thisRound[1]
            to_beat = thisRound[2]
        else:
            return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))
    # find questions and answers of current game
    if request.method == "GET":
        question = game["question"]
        answers = [game["correct_answer"], game["incorrect_answers"][0], game["incorrect_answers"][1], game["incorrect_answers"][2]]
        random.shuffle(answers)
        # check against who the player is playing
        if session.get("user_id") == players[0]["player1_id"]:
            opponent = find_username(players[0]["player2_id"])
        elif session.get("user_id") == players[0]["player2_id"]:
            opponent = find_username(players[0]["player1_id"])
        return render_template("play.html", question=question, answers=answers, to_beat=to_beat, opponent=opponent, score=score)
    else:
        # if the user answered all questions correct, end their turn
        if score >= 50:
            update_score(score, game_id, "active")
            score = 0
            game_id = 0
            finished = 5
            return redirect(url_for("index"))
        else:
            # increase the score when the user gives the right answer
            if request.form.get("answer") == game["correct_answer"]:
                score += 1
                return redirect(url_for('play'))
            else:
                # when the user doesn't give the right answer, check who is playing (player 1 or player 2)
                if to_beat == 999:
                    # if player 1 is playing, save their score
                    update_score(score, game_id, "active")
                    score = 0
                    game_id = 0
                    finished = [1, game["correct_answer"]]
                    return redirect(url_for("index"))
                else:
                    # if player 2 is playing, check who won
                    if to_beat > score:
                        # create the result
                        winner = find_username(players[0]["player1_id"])
                        loser = find_username(session.get("user_id"))
                        result = winner + " " + str(to_beat) + "-" + str(score) + " " + loser
                        finish_game(result, game_id)
                        # reset variables
                        score = 0
                        game_id = 0
                        finished = [2, game["correct_answer"]]
                        # add a win to the correct users' profile
                        increase_won(players[0]["player1_id"])
                        return redirect(url_for("index"))
                    elif to_beat < score:
                        # create the result
                        winner = find_username(session.get("user_id"))
                        loser = find_username(players[0]["player1_id"])
                        result = loser + " " + str(to_beat) + "-" + str(score) + " " + winner
                        finish_game(result, game_id)
                        # reset variables
                        score = 0
                        game_id = 0
                        finished = [3, game["correct_answer"]]
                        # add a win to the correct users' profile
                        increase_won(session.get("user_id"))
                        return redirect(url_for("index"))
                    elif to_beat == score:
                        # create the result
                        result = "Draw: " + "(" + str(score) + "-" + str(to_beat) + ")"
                        finish_game(result, game_id)
                        # reset variables
                        score = 0
                        game_id = 0
                        finished = [4, game["correct_answer"]]
                        return redirect(url_for("index"))


@app.route("/find_game", methods=["GET", "POST"])
@login_required
def find_game():
    """Allow the user to search for opponents"""
    # create variables
    global game_id
    global results
    global score
    global finished
    finished = 0
    score = 0
    if request.method == "GET":
        return render_template("find_game.html")
    else:
        # if the user typed in a username, look it up in the database
        if request.form['find_button'] == 'search':
            username = request.form.get("user")
            results = search_user(username)
            # if the username exists, save it and show the user the results
            return redirect(url_for("browse_users"))
        # if the user chooses a random user, get all ids from the databse
        elif request.form['find_button'] == 'random':
            ids = all_ids()
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
    # create variables
    global results
    global game_id
    global finished
    finished = 0
    if request.method == "POST":
        # find which user was invited
        invite_id = int(request.form.get("invite_id"))
        # check input
        if invite_id == session.get("user_id"):
            error = "Unable to invite yourself"
            return render_template("browse_users.html", results=results, error=error)
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
    """Shows the user their recent matches."""
    global score
    global finished
    finished = 0
    score = 0
    # find the users' recent games that are done
    history = user_history(session.get("user_id"))
    # find the usernames of the players involved in the matches
    for game in range(len(history)):
        matchup = find_matchup(history[game]["game_id"])
        history[game]["matchup"] = matchup[0]["player1_name"] + " vs. " + matchup[0]["player2_name"]
    return render_template("history.html", history=history)


@app.route("/leaderboard", methods=["GET"])
@login_required
def leaderboard():
    """Shows the 8 players with the most games won."""
    # create variables
    global score
    global finished
    finished = 0
    score = 0
    # find the top 8 players
    hoogste = highest()
    return render_template("leaderboard.html", hoogste=hoogste)
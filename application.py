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
import string

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Find all the games where the current user is player 1 or player 2. Also allow the user to join the games in which it's their turn."""
    session["score"] = 0
    # finished == 1 means wrong answer, 2 means lost, 3 means won, 4 means draw, 5 means all answers correct
    finished = session.get("finished")

    # show the user's current games, or sent them to the game they clicked on
    if request.method == "GET":
        # get the user's current games
        user_index = index_info(session.get("user_id"))
        rows = user_index[0]
        rows2 = user_index[1]

        if rows or rows2:
            return render_template("index.html", current=rows, current2=rows2, finished=finished)
        else:
            return render_template("index.html", finished=finished)
    else:
        # find on which game the user clicked and send them to that game
        tried_id = int(request.form.get("game_id"))

        # make sure the user hasn't altered game_ids
        if has_access(tried_id, session.get("user_id")):
            session["game_id"] = tried_id
            return redirect(url_for("play"))
        else:
            return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Compare a username and password against the database and let the user log in if both are correct."""

    # forget any user_id
    session.clear()

    # validate input
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("login.html", loginerror=1)
        elif not request.form.get("password"):
            return render_template("login.html", loginerror=2)
        rows = find_rows(request.form.get("username"))
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return render_template("login.html", loginerror=3)

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/forgottenpassword", methods=["GET", "POST"])
def forgottenpassword():
    """Send a user an email with a new randomly generated password."""
    # For this function to work, one must follow the steps provided in the send_mail function in helpers.py

    # Find the user that wants their password reset, create a password, and send an email
    if request.method == "POST":
        requester_mail = request.form.get("email")
        user_id = mail_to_id(requester_mail)

        # Make sure an account with the given email exists
        if user_id:
            new_password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
            reset_password(pwd_context.hash(new_password), user_id)
            try:
                send_mail(requester_mail, new_password)
                return render_template("login.html")
            except:
                return render_template("forgottenpassword.html", mailError=2)
        else:
            return render_template("forgottenpassword.html", mailError=1)
    else:
        return render_template("forgottenpassword.html", mailError=0)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Check the user-input and create an account with said input if no errors occured."""
    if request.method == "POST":
        # test user input
        if not request.form.get("username"):
            return render_template("register.html", regError=1)
        elif not request.form.get("password"):
            return render_template("register.html", regError=2)
        elif not request.form.get("confirmation"):
            return render_template("register.html", regError=3)
        elif not request.form.get("mail"):
            return render_template("register.html", regError=4)
        elif request.form.get("confirmation") != request.form.get("password"):
            return render_template("register.html", regError=5)
        if "@" not in request.form.get("mail"):
            return render_template("register.html", regError=6)

        # check to see whether username/mail already exists
        elif len(check_exists(request.form.get("username"))):
            return render_template("register.html", regError=7)
        elif mail_exists(request.form.get("mail")):
            return render_template("register.html", regError=8)

        games_won = 0

        # add user to database
        create_user(request.form.get("username"), pwd_context.hash(
            request.form.get("password")), games_won, request.form.get("mail"))
        return redirect(url_for("login"))
    else:
        return render_template("register.html", regError=0)


@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    """Let the user answer question in a streak, checking their answer and increment their score after each turn.
    Whenever a user makes a mistake, check who is playing and safe their score/end the game based on that."""

    # initialize game
    score = session.get("score")
    session["finished"] = 0
    game_id = session.get("game_id")

    # make sure the user is joining a valid game and is still on a valid turn
    if game_id > 0:
        thisRound = init_game(game_id)
        if score >= 50 and thisRound:
            all_correct(game_id, thisRound[2], session.get("user_id"), thisRound[1])
            reset_session(5, "n/a")
            return redirect(url_for("index"))
        elif thisRound:
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
        # increase the score when the user gives the right answer
        if request.form.get("answer") == game["correct_answer"]:
            session["score"] = session.get("score") + 1
            return redirect(url_for('play'))
        else:

            # when the user doesn't give the right answer, check who is playing (player 1 or player 2)
            if to_beat == 999:
                # if player 1 is playing, save their score and reset variables
                update_score(score, game_id, "active")
                reset_session(1, game["correct_answer"])

                return redirect(url_for("index"))
            else:
                # If player 2 is playing, save the result
                result = create_result(find_username(players[0]["player1_id"]), to_beat,
                                       score, find_username(session.get("user_id")))
                finish_game(result, game_id)

                # Check who won, add a win to that player's profile, and reset variables
                if to_beat > score:
                    reset_session(2, game["correct_answer"])
                    increase_won(players[0]["player1_id"])
                    return redirect(url_for("index"))
                elif to_beat < score:
                    reset_session(3, game["correct_answer"])
                    increase_won(session.get("user_id"))
                    return redirect(url_for("index"))
                elif to_beat == score:
                    result = F"Draw: {to_beat}-{score}"
                    finish_game(result, game_id)
                    reset_session(4, game["correct_answer"])
                    return redirect(url_for("index"))


@app.route("/find_game", methods=["GET", "POST"])
@login_required
def find_game():
    """Allow the user to search for opponents based on their username. The search is not case sensitive and uses wildcards."""
    # set variables
    session["score"] = 0
    session["finished"] = 0

    if request.method == "GET":
        return render_template("find_game.html")
    else:
        # look the username up in the database and show the user the results
        username = request.form.get("user")
        session["results"] = search_user(username)
        return redirect(url_for("browse_users"))


@app.route("/browse_users", methods=["GET", "POST"])
@login_required
def browse_users():
    """Show the user the users matching their search request, get said user's IDs and let the searching user invite others based on their ID."""
    # set variables
    results = session.get("results")
    session["finished"] = 0
    session["score"] = 0

    if request.method == "POST":
        # check which button was pressed
        if request.form["invite_id"] != "back":
            # find which user was invited
            invite_id = int(request.form.get("invite_id"))

            # check input
            if invite_id == session.get("user_id"):
                return render_template("browse_users.html", results=results, error="Unable to invite yourself")
            else:
                # start a game and save the game id
                session["game_id"] = create_game(session.get("user_id"), invite_id)
                return redirect(url_for("play"))
        else:
            return redirect(url_for("find_game"))
    else:
        return render_template("browse_users.html", results=results)


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Shows the user their 8 most recent matches."""
    # set variables
    session["score"] = 0
    session["finished"] = 0

    # find the user's recent games that are done
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
    # set variables
    session["score"] = 0
    session["finished"] = 0

    # find the top 8 players
    hoogste = highest()
    return render_template("leaderboard.html", hoogste=hoogste)


@app.route("/_instaplay", methods=["GET"])
@login_required
def instaplay():
    """Select a random user from the database based on ID and create a game with the current user and them."""
    # set variables
    session["score"] = 0
    session["finished"] = 0

    # get all ids from the databse
    ids = all_ids()

    # choose a random id
    random_id = random.randrange(len(ids))
    invite_id = ids[random_id]["id"]

    # keep choosing a random id while the random id is the same as the user's id
    while invite_id == session.get("user_id"):
        random_id = random.randrange(len(ids))-1
        invite_id = ids[random_id]["id"]

    # create a game with the user id and the random id and look up the game id
    session["game_id"] = create_game(session.get("user_id"), invite_id)
    return redirect(url_for("play"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Change password of the user"""
    # set variables
    session["score"] = 0
    session["finished"] = 0

    username = find_username(session.get("user_id"))
    games_won = find_won(session.get("user_id"))
    played_games = total_games(session.get("user_id"))

    # ensure valid input
    if request.method == "POST":
        if not request.form.get("newpassword"):
            return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=1)
        elif not request.form.get("confirmnewpassword"):
            return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=2)
        elif not request.form.get("newpassword") == request.form.get("confirmnewpassword"):
            return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=3)
        elif not correct_password(request.form.get("oldpassword"), session.get("user_id")):
            return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=4)
        else:
            # update the user's password and let them know
            reset_password(pwd_context.hash(request.form.get("newpassword")), session.get("user_id"))
            return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=5)
    else:
        return render_template("profile.html", username=username, games_won=games_won, played_games=played_games, validate_input=0)
import csv
import urllib.request

from flask import redirect, render_template, request, session
from functools import wraps

import requests
import random
from cs50 import SQL
import ast

db = SQL("sqlite:///trivia.db")


def create_game(player1_id, player2_id):
    """Create a game between two players."""
    # haal vragen op
    vragen = requests.get("https://opentdb.com/api.php?amount=50&category=22&type=multiple")
    # zet vragen in json
    json = vragen.json()
    # shuffle de vragen
    random.shuffle(json["results"])
    # insert de benodigde gegevens in de database
    player1_name = db.execute("SELECT username FROM users WHERE id = :player1_id", player1_id=player1_id)[0]["username"]
    player2_name = db.execute("SELECT username FROM users WHERE id = :player2_id", player2_id=player2_id)[0]["username"]
    db.execute("INSERT INTO games (player1_id, player2_id, questions, player1_name, player2_name) VALUES (:player1_id, :player2_id, :questions, :player1_name, :player2_name)",
               player1_id=player1_id, player2_id=player2_id, questions=str(json), player1_name=player1_name, player2_name=player2_name)
    return db.execute("SELECT max(game_id) FROM games WHERE player1_id = :player1_id AND player2_id = :player2_id",
                      player1_id=player1_id, player2_id=player2_id)[0]["max(game_id)"]


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def find_username(user_id):
    """find the username for a given user_id."""
    return str(db.execute("SELECT username FROM users WHERE id = :user_id", user_id=user_id)[0]["username"])


def finish_game(result, game_id):
    """End the game."""
    # save the results
    db.execute("UPDATE games SET status = :status WHERE game_id = :game_id", status=result, game_id=game_id)
    # remove the questions from the database in order to save space
    db.execute("UPDATE games SET questions = :leeg WHERE game_id = :game_id", leeg="n/a", game_id=game_id)


def index_info(user_id):
    """Find the games in which the user is participating."""
    # games that the user has made
    sent = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player1_id = :id and status = :active",
                      id=session["user_id"], active=("active"))
    # games that the user was invited to
    received = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player2_id = :id and status = :active",
                          id=session["user_id"], active=("active"))
    return [sent, received]


def init_game(game_id):
    """Get the needed information for the game."""
    # find the questions for the game
    questionCol = db.execute("SELECT questions FROM games WHERE game_id = :game_id",
                             game_id=game_id)[0]["questions"]
    # if there are questions, find them, find the players and find the score that needs to be beat
    if questionCol != "n/a":
        questions = ast.literal_eval(questionCol)
        players = db.execute("SELECT player1_id, player2_id FROM games WHERE game_id = :game_id", game_id=game_id)
        to_beat = db.execute("SELECT score FROM games WHERE game_id = :game_id", game_id=game_id)[0]["score"]
        return [questions, players, to_beat]
    else:
        return False

def send_mail(requester_mail,new_password):
    import smtplib, ssl
    "Set up the connection to send the e-mail and "
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "GeographyGuruRecovery@gmail.com"
    password = "webIK201904"
    subject="Geography Guru Password Reset"
    message = """\
    Dear user,

    A new password was requested.
    Your new password is: """+new_password+"""

    We hope to see you back again soon. Maybe you should play the game a bit more. Maybe then you wouldn't forget your password as often!
    """
    text='Subject: {}\n\n{}'.format(subject, message)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, requester_mail, text)

def update_score(score, game_id, status):
    """Update the score after the first player is finished."""
    db.execute("UPDATE games SET score = :score, status = :status WHERE game_id = :game_id",
               score=score, game_id=game_id, status=status)


def search_user(username):
    """find the information of a user (after searching for opponents)"""
    return db.execute("SELECT id, username FROM users WHERE username LIKE :username COLLATE NOCASE LIMIT 10", username=username+"%")


def user_history(user_id):
    """find the most recent games the user has participated in."""
    return db.execute("SELECT game_id, status FROM games WHERE (status != 'active' AND status != 'starting') AND (player1_id = :user_id OR player2_id = :user_id) ORDER BY game_id DESC LIMIT 10", user_id=session.get("user_id"))


def find_matchup(game_id):
    """Find the usernames of the match participants"""
    return db.execute("SELECT player1_name, player2_name FROM games WHERE game_id = :game_id", game_id=game_id)


def find_won(user_id):
    """find how many games the user has won."""
    return int(db.execute("SELECT games_won FROM users WHERE id = :user_id", user_id=user_id)[0]["games_won"])


def increase_won(user_id):
    """"Increases the amount of games the user has won by 1."""
    db.execute("UPDATE users SET games_won = games_won + 1 WHERE id = :user_id", user_id=user_id)


def highest():
    """Look up the users with the most games won."""
    return db.execute("SELECT username, games_won FROM users ORDER BY games_won DESC LIMIT 8")


def has_access(game_id, user_id):
    """Check to make sure users don't join games they aren't supposed to."""
    legit_player = db.execute("SELECT player2_id FROM games WHERE game_id = :game_id", game_id=game_id)[0]["player2_id"]
    return legit_player == user_id


def find_rows(username):
    """Find the information of a user by username"""
    return db.execute("SELECT * FROM users WHERE username = :username COLLATE NOCASE", username=username)


def create_user(username, hashed, games_won,mail):
    """Adds a new user to the database."""
    db.execute("INSERT INTO users (username, hash, games_won,mail) VALUES (:username, :hashed, :games_won,:mail)",
               username=username, hashed=hashed, games_won=games_won,mail=mail)


def check_exists(username):
    """Check if a username is already taken."""
    return db.execute("SELECT id FROM users WHERE username = :username;", username=username)


def all_ids():
    """Return all user_ids in the database."""
    return db.execute("SELECT id FROM users")

def find_email(username):
    """Find the email address associated with a given username."""
    return db.execute("select mail from users where username=:username COLLATE NOCASE", username=username)

def reset_password(new_password, username):
    """Update a user's password."""
    db.execute("update users set hash=:password where username=:username", password=new_password, username=username)

def all_correct(game_id, to_beat, user_id, players):
    """Handles the edge case in which a user has all questions correct."""
    # check which round the player is in and if they won/drew
    if to_beat == 999:
        update_score(50, game_id, "active")
    elif to_beat < 50:
        winner = find_username(session.get("user_id"))
        loser = find_username(players[0]["player1_id"])
        result = winner + " " + str(50) + "-" + str(to_beat) + " " + loser
        finish_game(result, game_id)
    elif to_beat == 50:
        result = "Draw: " + "(" + str(50) + "-" + str(50) + ")"
        finish_game(result, game_id)
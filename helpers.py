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
    return str(db.execute("SELECT username FROM users WHERE id = :user_id", user_id=user_id)[0]["username"])

def finish_game(result, game_id):
    db.execute("UPDATE games SET status = :status WHERE game_id = :game_id", status=result, game_id=game_id)

def index_info(user_id):
    sent = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player1_id = :id and status = :active",
                      id=session["user_id"], active=("active"))
    received = db.execute("SELECT game_id, player1_name, player2_name, score, status FROM games WHERE player2_id = :id and status = :active",
                       id=session["user_id"], active=("active"))
    return [sent, received]

def init_game(game_id):
    questions = ast.literal_eval(db.execute("SELECT questions FROM games WHERE game_id = :game_id",
                                            game_id=game_id)[0]["questions"])
    players = db.execute("SELECT player1_id, player2_id FROM games WHERE game_id = :game_id", game_id=game_id)
    to_beat = db.execute("SELECT score FROM games WHERE game_id = :game_id", game_id=game_id)[0]["score"]
    return [questions, players, to_beat]

def update_score(score, game_id, status):
    db.execute("UPDATE games SET score = :score, status = :status WHERE game_id = :game_id",
                       score=score, game_id=game_id, status=status)

def search_user(username):
    return db.execute("SELECT id, username FROM users WHERE username LIKE :username COLLATE NOCASE LIMIT 10", username=username+"%")

def user_history(user_id):
    return db.execute("SELECT game_id, status FROM games WHERE (status != 'active' AND status != 'starting') AND (player1_id = :user_id OR player2_id = :user_id) LIMIT 20", user_id=session.get("user_id"))

def find_matchup(game_id):
    return db.execute("SELECT player1_name, player2_name FROM games WHERE game_id = :game_id", game_id=game_id)
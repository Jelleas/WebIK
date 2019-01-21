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


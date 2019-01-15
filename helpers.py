import csv
import urllib.request

from flask import redirect, render_template, request, session
from functools import wraps

import requests
import random
from cs50 import SQL
import ast

db = SQL("sqlite:///geo_guru.db")

def create_game(user_id, invite_id):

    # haal vragen op
    vragen = requests.get("https://opentdb.com/api.php?amount=50&category=22&type=multiple")
    # zet ze in json
    json = vragen.json()
    # insert de benodigde gegevens in de database
    db.execute("INSERT INTO games (user_id, invite_id, score, questions) VALUES (:user_id, :invite_id, :score, :questions)", user_id=user_id, invite_id=invite_id, score=0, questions=str(json))


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


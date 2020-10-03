from flask import Flask, render_template, request, session
from flask_session import Session
from riotwatcher import LolWatcher, ApiError
import main
import pandas as pd


app = Flask(__name__)
# i actually got a production api key approved from riot
api_key = 'PASTE-YOUR-RIOT-API-KEY-HERE'
watcher = LolWatcher(api_key)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)


@app.route('/', methods=['GET', 'POST'])
def my_form():
    if session.get('level'):
        session.clear()
    return render_template('website.html')


@app.route('/overview', methods=['GET', 'POST'])
def overview():
    if not session.get('level'):
        main.fetch_stats()
    return render_template('my_layout/index.html')


@app.route('/match_history', methods=['GET', 'POST'])
def match_history():
    return render_template('my_layout/match_history.html')


@app.route('/live', methods=['GET', 'POST'])
def live():
    return render_template('my_layout/live_game.html')


@app.errorhandler(500)
def page_not_found(e):
    return render_template('my_layout/not_found.html'), 500

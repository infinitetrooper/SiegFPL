# app.py
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
import json
import pandas as pd
from src.get_data import fetch_team_gw_data
from src.load_data import load_team_data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    team_id = request.form.get('team_id')
    game_week = request.form.get('game_week')
    
    try:
        fetch_team_gw_data(gw=game_week, team_id=team_id)
        team_data = load_team_data(gw=game_week, team_id=team_id)
        return render_template('result.html', team_data=team_data.to_html())
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request
from src.main import get_best_squad

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        team_id = request.form['team_id']
        game_week = request.form['game_week']
        free_transfers = request.form['free_transfers']
        wildcard = request.form.get('wildcard') == 'on'

        try:
            squad, best_11, captain, predicted_points = get_best_squad(
                int(team_id), int(game_week), int(free_transfers), wildcard)
            result = {
                'squad': squad,
                'best_11': best_11,
                'captain': captain,
                'predicted_points': predicted_points
            }
        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
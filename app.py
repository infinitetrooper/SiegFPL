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
            squad, best_11, captain, predicted_points, transfers = get_best_squad(int(team_id), int(game_week), int(free_transfers), wildcard)
            predicted_points = round(predicted_points)
            total_cost = squad['value'].sum()
            
            # Sort squad and best_11 lists in order of GK, DEF, MID, FWD
            position_order = {'GK': 1, 'DEF': 2, 'MID': 3, 'FWD': 4}
            squad = squad.sort_values(by='position', key=lambda x: x.map(position_order.get))
            best_11 = best_11.sort_values(by='position', key=lambda x: x.map(position_order.get))
            
            result = {
                'squad': squad,
                'best_11': best_11,
                'captain': captain,
                'predicted_points': predicted_points,
                'transfers': transfers,
                'total_cost': total_cost
            }
        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)

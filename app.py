from flask import Flask, render_template, request
from src.main import get_best_squad, get_best_possible_squad
from src.player_positioning import position_players

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        team_id = request.form['team_id']
        free_transfers = request.form['free_transfers']
        wildcard = request.form.get('wildcard') == 'on'

        try:
            result = process_squad_data(team_id, free_transfers, wildcard)
        except Exception as e:
            error = str(e)
    else:
        try:
            result = process_squad_data(None, 0, True)
        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, error=error)

def process_squad_data(team_id, free_transfers, wildcard):
    if wildcard:
        squad, best_11_df, captain, predicted_points, transfers = get_best_possible_squad()
    else:
        squad, best_11_df, captain, predicted_points, transfers = get_best_squad(int(team_id), int(free_transfers), wildcard)
    
    predicted_points = round(predicted_points)
    total_cost = squad['value'].sum()

    # Sort squad and best_11 DataFrames
    position_order = {'GK': 1, 'DEF': 2, 'MID': 3, 'FWD': 4}
    squad = squad.sort_values(by='position', key=lambda x: x.map(position_order.get))
    best_11_df = best_11_df.sort_values(by='position', key=lambda x: x.map(position_order.get))

    # Convert DataFrames to list of dictionaries
    squad = squad.to_dict('records')
    best_11 = best_11_df.to_dict('records')

    # Position players on the pitch
    best_11 = position_players(best_11)

    return {
        'squad': squad,
        'best_11': best_11,
        'captain': captain,
        'predicted_points': predicted_points,
        'transfers': transfers,
        'total_cost': total_cost
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)

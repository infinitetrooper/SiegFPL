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
            squad, best_11_df, captain, predicted_points, transfers = get_best_squad(int(team_id), int(game_week), int(free_transfers), wildcard)
            predicted_points = round(predicted_points)
            total_cost = squad['value'].sum()

            # Sort squad and best_11 DataFrames
            position_order = {'GK': 1, 'DEF': 2, 'MID': 3, 'FWD': 4}
            squad = squad.sort_values(by='position', key=lambda x: x.map(position_order.get))
            best_11_df = best_11_df.sort_values(by='position', key=lambda x: x.map(position_order.get))

            
            # Print all the column names in best_11_df using a loop
            for column in best_11_df.columns:
                print(column)
            
            # Convert DataFrames to list of dictionaries
            squad = squad.to_dict('records')
            best_11 = best_11_df.to_dict('records')

            result = {
                'squad': squad,
                'best_11': best_11,
                'captain': captain,
                'predicted_points': predicted_points,
                'transfers': transfers,
                'total_cost': total_cost
            }

            # Prepare player positions for the pitch
            positions = {
                'GK': [50],
                'DEF': [20, 40, 60, 80],
                'MID': [15, 35, 55, 75, 95],
                'FWD': [30, 50, 70]
            }
            for position in positions:
                players = [p for p in best_11 if p['position'] == position]
                for i, player in enumerate(players):
                    player['x'] = positions[position][i]

        except Exception as e:
            error = str(e)

        
        return render_template('pitch.html', best_11=best_11)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, threaded=True)

from flask import Flask, render_template, request
from src.main import get_best_squad

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        team_id = request.form['team_id']
        game_week = request.form['game_week']
        wildcard = request.form.get('wildcard') == 'on'
        
        try:
            squad, best_11, captain, predicted_points = get_best_squad(int(team_id), int(game_week), wildcard)
            return render_template('result.html', squad=squad, best_11=best_11, captain=captain, predicted_points=predicted_points)
        except Exception as e:
            error_message = str(e)
            return render_template('index.html', error=error_message)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
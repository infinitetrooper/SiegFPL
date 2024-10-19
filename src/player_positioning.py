# src/player_positioning.py

def position_players(best_11):
    total_widths = calculate_total_widths(best_11)
    
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        players = [p for p in best_11 if p['position'] == position]
        num_players = len(players)
        if num_players > 0:
            x_positions = calculate_x_positions(position, num_players, total_widths)
            for i, player in enumerate(players):
                player['x'] = x_positions[i]
    
    return best_11

def calculate_total_widths(best_11):
    total_widths = {}
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        num_players = len([p for p in best_11 if p['position'] == position])
        if num_players <= 1:
            total_widths[position] = 0
        elif num_players <= 2:
            total_widths[position] = num_players * 30
        elif num_players <= 3:
            total_widths[position] = num_players * 20
        else:
            total_widths[position] = num_players * 15
    return total_widths

def calculate_x_positions(position, num_players, total_widths):
    if num_players == 1:
        return [50]  # Center position
    else:
        total_width = total_widths.get(position, 40)
        start_x = 50 - (total_width / 2)
        if num_players == 2:
            return [50 - (total_width / 4), 50 + (total_width / 4)]
        else:
            spacing = total_width / (num_players - 1)
            return [start_x + i * spacing for i in range(num_players)]
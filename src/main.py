from src.build_squad import pick_best_squad, get_eligible_players_for_gw
from src.load_data import load_and_filter_data, load_team_data, load_latest_data

def get_best_squad(team_id, free_transfers, wildcard=False):
    game_week = get_gameweek()
    try:
        latest_data = load_latest_data()["elements"]
        fpl_data = load_and_filter_data(year="2024-25", min_minutes=60, min_gw=5)
        eligible_players = get_eligible_players_for_gw(gw=game_week, merged_gw_df=fpl_data, latest_data=latest_data)

        value = 1000
        
        if not wildcard:
            current_team, value = load_team_data(gw=game_week - 1, team_id=team_id)
        else:
            current_team = None

        squad, best_11, captain, transfers = pick_best_squad(player_data=eligible_players, prev_squad=current_team, free_transfers=free_transfers, transfer_threshold=4, budget=value)

        predicted_points = best_11["xPts"].sum() + captain["xPts"]

        return squad, best_11, captain, predicted_points, transfers

    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

def get_gameweek():
    # Fetch events data from FPL API
    data = load_latest_data()
    events = data['events']

    # Find current gameweek
    gw = 1  # Default to GW1 if no other match found

    for event in events:
        if event['is_next']:
            gw = event['id']
            break

    return gw

def get_best_possible_squad():
    """Get the best possible squad without any team constraints"""
    try:
        squad, best_11, captain, predicted_points, transfers = get_best_squad(None, 0, True)
        
        return squad, best_11, captain, predicted_points, transfers
    except Exception as e:
        return None, str(e)
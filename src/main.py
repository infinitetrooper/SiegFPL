from src.build_squad import pick_best_squad, get_eligible_players_for_gw
from src.load_data import load_and_filter_data, load_team_data
from src.load_data import load_latest_data

def get_best_squad(team_id, game_week, free_transfers, wildcard=False):
    try:
        fpl_data = load_and_filter_data(year="2024-25", min_minutes=60, min_gw=3)
        eligible_players = get_eligible_players_for_gw(gw=game_week, merged_gw_df=fpl_data, latest_data=load_latest_data())

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

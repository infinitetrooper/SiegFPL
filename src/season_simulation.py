import pandas as pd
from src.x_pts import calculate_expected_points, predict_future_xPts
from src.load_data import load_and_filter_data, load_team_data
from src.build_squad import pick_best_squad, handle_transfers, select_best_11, get_eligible_players_for_gw
import gc

def simulate_season_2023_24():
    # Load the initial data for the season
    season_data = load_and_filter_data(year="2023-24")
    season_points = 0
    initial_budget = 1000
    current_team = None

    for gw in range(1, 39):
        print(f"\nProcessing Gameweek {gw}...")

        if gw == 1:
            # For GW1, directly use ict_index to pick the initial squad
            eligible_players = season_data[season_data["GW"] == gw]
            criteria = "ict_index"
            squad, best_11, captain = pick_best_squad(player_data=eligible_players, budget=initial_budget,
                                                      criteria=criteria)
        else:
            # Get eligible players for the gameweek and the current team
            eligible_players = get_eligible_players_for_gw(gw=gw, merged_gw_df=season_data)

            # Build the squad for the week using previous data and transfers
            squad, best_11, captain = pick_best_squad(player_data=eligible_players, prev_squad=current_team)

        # Calculate the actual points for the best 11 players in this gameweek
        gw_actual_points = 0
        for _, player in best_11.iterrows():
            player_points = season_data[(season_data['GW'] == gw) & (season_data['element'] == player['element'])]['total_points']
            player_points = player_points.values[0] if not player_points.empty else 0
            gw_actual_points += player_points

        # Double the captain's points
        captain_points = season_data[(season_data['GW'] == gw) & (season_data['element'] == captain['element'])]['total_points']
        captain_points = captain_points.values[0] if not captain_points.empty else 0
        gw_actual_points += captain_points  # Add the captain's points again for doubling

        season_points += gw_actual_points

        print(f"Points for GW{gw}: {gw_actual_points}")

        # Update the current team for the next gameweek
        current_team = squad.copy()

        # Calculate the total squad cost
        total_squad_cost = squad['now_cost' if 'now_cost' in squad.columns else 'value'].sum()

        # Display the squad size, details, and total cost
        print(f"Squad of {len(squad)} players (Total Cost: {total_squad_cost}):")
        # Iterate through each player in the current team and fetch their points for the current game week
        player_details = []
        for _, player in current_team.iterrows():
            # Fetch the total points for the player for the current game week
            gw_points = season_data[
                (season_data['GW'] == gw) & (season_data['element'] == player['element'])
                ]['total_points'].values

            # Handle cases where no points are found for the player (e.g., if the player didn't play)
            gw_points = gw_points[0] if len(gw_points) > 0 else 0

            player_details.append(f"{player['name']} ({player['element']}, {player['position']}, {gw_points} points)")

        # Print the current team with total points for the game week
        print(f"Current team : {player_details}")

        # Clear data frames after each loop to manage memory
        del eligible_players, squad, best_11, captain
        gc.collect()

    # Print the total points accumulated for the season
    print(f"\nTotal points for the 2023-24 season: {season_points}")

    return season_points

if __name__ == "__main__":
    # Run the simulation
    simulate_season_2023_24()
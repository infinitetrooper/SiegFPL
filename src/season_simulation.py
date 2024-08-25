import pandas as pd
from src.x_pts import calculate_expected_points, predict_future_xPts
from src.load_data import load_and_filter_data, load_team_data
from src.build_squad import pick_best_squad, handle_transfers, select_best_11, get_eligible_players_for_gw
import gc


def simulate_season_2023_24():
    # Load the initial data for the season
    season_data = load_and_filter_data(year="2023-24")
    total_points = 0
    initial_budget = 1000
    free_transfers = 1
    transfer_penalty = 4
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
            eligible_players = get_eligible_players_for_gw(gw, season_data, season_data[season_data["GW"] == gw])

            # Build the squad for the week using previous data and transfers
            squad, best_11, captain = pick_best_squad(player_data=eligible_players, prev_squad=current_team)

        # Calculate the actual points for the best 11 players in this gameweek, with captain points doubled
        gw_actual_points = best_11["total_points"].sum() + captain["total_points"]
        total_points += gw_actual_points

        print(f"Points for GW{gw}: {gw_actual_points}")

        # Update the current team for the next gameweek
        current_team = squad.copy()

        # Clear data frames after each loop to manage memory
        del eligible_players, squad, best_11, captain
        gc.collect()

    # Print the total points accumulated for the season
    print(f"\nTotal points for the 2023-24 season: {total_points}")

    return total_points


if __name__ == "__main__":
    # Run the simulation
    simulate_season_2023_24()
from get_data import load_and_filter_data
from x_pts import calculate_expected_points, predict_future_xPts
from build_squad import pick_best_squad  # Assuming this is where the pick_best_squad function is defined


def simulate_fpl_season():
    # Load data for the 2023-24 season
    df = load_and_filter_data(year="2023-24")

    # Model expected points (xPts)
    coef, intercept = calculate_expected_points(df)

    # Initialize variables for simulation
    total_points = 0
    previous_squad = None

    # Loop through each game week
    for gw in range(1, 39):  # GW 1 to GW 38
        print(f"Simulating Game Week {gw}...")

        if gw == 1:
            # For GW 1, pick the best squad based on highest ICT index
            squad, starting_11, captain = pick_best_squad(df[df["GW"] == gw], budget=1000, criteria="total_points")
        else:
            # From GW 2 onwards, calculate 3-week average ICT
            df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(
                1).reset_index(level=0, drop=True)

            df["xPts"] = predict_future_xPts(df["avg_ict_last_3_gw"], coef, intercept)

            # Pick the squad based on 3-week average ICT and xPts
            squad, starting_11, captain = pick_best_squad(
                df[df["GW"] == gw],
                budget=1000,
                criteria="ict_index",
                avg_criteria="avg_ict_last_3_gw",
                prev_squad=previous_squad,
                transfer_threshold=4
            )

        # Calculate points for the starting 11 in the current game week
        gw_points = sum([player["total_points"] for _, player in starting_11.iterrows()])

        # Double the points for the captain
        gw_points += captain["total_points"]

        print(gw_points)

        # Add the game week points to the total points
        total_points += gw_points

        # Update the previous squad for the next iteration
        previous_squad = squad

    # Return the total points earned across all game weeks
    return total_points


if __name__ == "__main__":
    total_score = simulate_fpl_season()
    print(f"Total Score for the 2023-24 Season: {total_score}")

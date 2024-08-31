from build_squad import pick_best_squad, get_eligible_players_for_gw
from load_data import load_and_filter_data, load_team_data
from src.load_data import load_latest_data


def main():
    # Fetch FPL data
    gw = get_game_week()
    fpl_data = load_and_filter_data(year="2024-25", min_minutes=0, min_gw=0)
    eligible_players = get_eligible_players_for_gw(gw=gw, merged_gw_df=fpl_data, latest_data=load_latest_data())
    current_team = load_team_data(gw=gw-1)

    # Build the squad
    squad, best_11, captain = pick_best_squad(player_data=eligible_players, prev_squad=current_team, free_transfers=2, transfer_threshold=2)

    # Calculate predicted points (sum of starting 11 xPts with captain’s points doubled)
    predicted_points = best_11["xPts"].sum() + captain["xPts"]

    # Calculate the total squad cost
    total_squad_cost = squad['now_cost' if 'now_cost' in squad.columns else 'value'].sum()

    # Display the squad size, details, and total cost
    print(f"Squad of {len(squad)} players (Total Cost: {total_squad_cost}):")
    for _, player in squad.iterrows():
        print(
            f"{player['web_name' if 'web_name' in player else 'name']} - "
            f"Position: {player['position' if 'position' in player else 'element_type']} - "
            f"Cost: {player['now_cost' if 'now_cost' in player else 'value']} - "
            f"Points: {player['total_points']}"
        )

    # Display the best starting 11
    print("\nBest Starting 11:")
    for _, player in best_11.iterrows():
        print(
            f"{player['web_name' if 'web_name' in player else 'name']} - "
            f"Position: {player['position' if 'position' in player else 'element_type']} - "
            f"Cost: {player['now_cost' if 'now_cost' in player else 'value']} - "
            f"xPts: {player['xPts']}"
        )

    # Display the captain
    print(
        f"\nCaptain: {captain['web_name' if 'web_name' in captain else 'name']} - "
        f"xPts: {captain['xPts']} - "
        f"Cost: {captain['now_cost' if 'now_cost' in captain else 'value']}"
    )

    # Display the predicted points for the game week
    print(f"\nPredicted Points for the Game Week: {predicted_points:.2f}")

def get_game_week():
    """
    Prompts the user to input the game week number and returns it as an integer.

    Returns:
        int: The game week number entered by the user.
    """
    while True:
        try:
            gw = int(input("Enter the game week (e.g., 1, 2, 3): "))
            if gw < 1:
                print("Game week must be a positive number. Please try again.")
            else:
                return gw
        except ValueError:
            print("Invalid input. Please enter a valid game week number.")

if __name__ == "__main__":
    main()
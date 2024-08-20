from build_squad import pick_best_squad, get_eligible_players_for_gw
from get_data import load_and_filter_data

def main():
    # Fetch FPL data
    fpl_data = load_and_filter_data(year="2024-25", min_minutes=0, min_gw=0)
    eligible_players = get_eligible_players_for_gw(2, fpl_data)

    # Build the squad
    squad, best_11, captain = pick_best_squad(eligible_players)

    # Display the squad
    print("Squad of 15:")
    for _, player in squad.iterrows():
        print(f"{player['web_name' if 'web_name' in player else 'name']} - Position: {player['position' if 'position' in player else 'element_type']} - Cost: {player['now_cost' if 'now_cost' in player else 'value']} - ICT Index: {player['ict_index']}")

    # Display the best starting 11
    print("\nBest Starting 11:")
    for _, player in best_11.iterrows():
        print(f"{player['web_name' if 'web_name' in player else 'name']} - Position: {player['position' if 'position' in player else 'element_type']} - ICT Index: {player['ict_index']}")

    # Display the captain
    print(f"\nCaptain: {captain['web_name' if 'web_name' in captain else 'name']} - ICT Index: {captain['ict_index']} (Double Points)")

if __name__ == "__main__":
    main()

# main.py

from get_data import get_fpl_data
from build_squad import pick_best_squad

def main():
    # Fetch FPL data
    fpl_data = get_fpl_data('github')
    if not fpl_data:
        print("Failed to fetch FPL data.")
        return

    # Build the squad
    squad, best_11, captain = pick_best_squad(fpl_data)

    # Display the squad
    print("Squad of 15:")
    for player in squad:
        print(f"{player['web_name']} - Position: {player['element_type']} - Cost: {player['now_cost']} - ICT Index: {player['ict_index']}")

    # Display the best starting 11
    print("\nBest Starting 11:")
    for player in best_11:
        print(f"{player['web_name']} - Position: {player['element_type']} - ICT Index: {player['ict_index']}")

    # Display the captain
    print(f"\nCaptain: {captain['web_name']} - ICT Index: {captain['ict_index']} (Double Points)")

if __name__ == "__main__":
    main()

import pandas as pd
from src.build_squad import get_eligible_players_for_gw, pick_best_squad
from src.load_data import load_and_filter_data, load_latest_data

def simulate_season_2023_24(team_id=None, initial_budget=1000):
    """
    Simulates the 2023-24 FPL season using historical data.
    
    Args:
        team_id (int, optional): Team ID to track for comparison
        initial_budget (int): Starting budget (default 1000)
    
    Returns:
        tuple: Total points and gameweek breakdown
    """
    # Load the season data
    season_data = load_and_filter_data(year="2023-24")
    latest_data = load_latest_data()
    
    season_points = 0
    gameweek_points = []
    current_team = None
    current_budget = initial_budget
    free_transfers = 1

    for gw in range(1, 39):
        print(f"\nProcessing Gameweek {gw}...")

        try:
            if gw == 1:
                # For GW1, use ict_index to pick initial squad
                eligible_players = season_data[season_data["GW"] == gw].copy()
                squad, best_11, captain, transfers = pick_best_squad(
                    player_data=eligible_players,
                    budget=current_budget,
                    criteria="ict_index"
                )
            else:
                # Get eligible players and make transfers
                eligible_players = get_eligible_players_for_gw(
                    gw=gw,
                    merged_gw_df=season_data,
                    latest_data=latest_data
                )
                
                squad, best_11, captain, transfers = pick_best_squad(
                    player_data=eligible_players,
                    budget=current_budget,
                    prev_squad=current_team,
                    free_transfers=free_transfers
                )

            # Update free transfers for next week
            free_transfers = 2 if len(transfers) == 0 else 1

            # Calculate actual points for the gameweek
            gw_points = 0
            transfer_cost = max(0, (len(transfers) - free_transfers) * 4)
            
            # Calculate points for the best 11 including captain
            for _, player in best_11.iterrows():
                player_gw_data = season_data[
                    (season_data['GW'] == gw) & 
                    (season_data['element'] == player['element'])
                ]
                
                if not player_gw_data.empty:
                    points = player_gw_data['total_points'].iloc[0]
                    # Double points for captain
                    if player['element'] == captain['element']:
                        points *= 2
                    gw_points += points

            # Subtract transfer costs
            gw_points -= transfer_cost
            
            # Update season totals
            season_points += gw_points
            gameweek_points.append({
                'GW': gw,
                'Points': gw_points,
                'Transfers': len(transfers),
                'Transfer_Cost': transfer_cost,
                'Captain': captain['web_name'] if 'web_name' in captain else captain['name']
            })
            
            # Update current team for next iteration
            current_team = squad
            
            print(f"GW{gw} Points: {gw_points} (Transfers: {len(transfers)}, Cost: -{transfer_cost})")
            print(f"Captain: {captain['web_name'] if 'web_name' in captain else captain['name']}")
            print(f"Season Total: {season_points}")

        except Exception as e:
            print(f"Error in GW{gw}: {str(e)}")
            continue

    print(f"\nFinal Season Points: {season_points}")
    return season_points, pd.DataFrame(gameweek_points)

if __name__ == "__main__":
    total_points, gw_breakdown = simulate_season_2023_24()
    print("\nGameweek Breakdown:")
    print(gw_breakdown)
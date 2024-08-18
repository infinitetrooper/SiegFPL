import pandas as pd

def pick_best_squad(data, budget=1000, criteria="ict_index", avg_criteria=None, prev_squad=None, transfer_threshold=4):
    """
    Pick the best squad based on a specified criteria (e.g., ICT index or 3-week average ICT).
    Supports transfer logic and flexible squad composition.

    :param data: The player data for the specific game week as a DataFrame.
    :param budget: The budget for the squad (default is 1000).
    :param criteria: The criteria used to sort and select players (e.g., "ict_index", "avg_ict_last_3_gw").
    :param avg_criteria: Optional criteria for calculating averages across weeks (used for rolling averages).
    :param prev_squad: The squad from the previous game week (used for transfers).
    :param transfer_threshold: The minimum difference in xPts required to make a transfer (default is 4).
    :return: The selected squad, best 11, and the captain.
    """

    # Determine whether to use 'position' or 'element_type' based on availability
    if 'position' in data.columns:
        position_col = 'position'
    elif 'element_type' in data.columns:
        position_col = 'element_type'
    else:
        raise ValueError("Neither 'position' nor 'element_type' column found in the data.")

    # Map element_type to position names if 'element_type' is used
    if position_col == 'element_type':
        data['position'] = data['element_type'].map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})

    # Determine which column to use for the player name (web_name or name)
    name_column = 'web_name' if 'web_name' in data.columns else 'name'

    # Sort players based on the specified criteria
    if avg_criteria:
        data = data.sort_values(by=avg_criteria, ascending=False)
    else:
        data = data.sort_values(by=criteria, ascending=False)

    # Determine which column to use for cost
    cost_column = 'now_cost' if 'now_cost' in data.columns else 'value'

    # Filter players based on their position
    goalkeepers = data[data['position'] == 'GK'].head(10)
    defenders = data[data['position'] == 'DEF'].head(25)
    midfielders = data[data['position'] == 'MID'].head(25)
    forwards = data[data['position'] == 'FWD'].head(15)

    # Pick the best 2 goalkeepers, 5 defenders, 5 midfielders, and 3 forwards within the budget
    selected_goalkeepers = goalkeepers.head(2)
    selected_defenders = defenders.head(5)
    selected_midfielders = midfielders.head(5)
    selected_forwards = forwards.head(3)

    squad = pd.concat([selected_goalkeepers, selected_defenders, selected_midfielders, selected_forwards])

    # Run simulations until a squad within the budget is found
    while True:
        squad_cost = squad[cost_column].sum()

        if squad_cost <= budget:
            print("Final Squad Cost: ", squad_cost)
            break  # Exit loop if budget is satisfied

        # If the budget is exceeded, attempt to replace the player with the least value in the chosen criteria
        for _, player in squad.sort_values(by=avg_criteria or criteria).iterrows():
            available_replacements = data[(data['position'] == player['position']) &
                                          (~data.index.isin(squad.index)) &
                                          (data[cost_column] < player[cost_column])]

            if not available_replacements.empty:
                # Replace the player with the best available replacement based on the chosen criteria
                replacement = available_replacements.sort_values(by=avg_criteria or criteria, ascending=False).iloc[0]
                squad = squad.drop(player.name)
                squad = pd.concat([squad, replacement.to_frame().T])
                break
        else:
            # If no valid replacements are found, the squad remains unchanged
            break

    # Handle transfers: Only transfer if the difference in xPts is greater than the threshold
    if prev_squad is not None:
        for _, player in prev_squad.iterrows():
            if player.name in squad.index:
                new_player = squad.loc[player.name]
                if (new_player["position"] == player["position"] and
                    new_player[cost_column] <= player[cost_column] and
                    new_player.get("xPts", 0) - player.get("xPts", 0) < transfer_threshold):
                    squad.loc[player.name] = player  # Revert to the original player if the transfer doesn’t meet the threshold

    # From this squad, pick the best 11 with at least 1 GK, 3 DEF, 3 MID, and 1 FWD
    selected_goalkeepers = squad[squad['position'] == 'GK'].head(1)
    selected_defenders = squad[squad['position'] == 'DEF'].head(3)
    selected_midfielders = squad[squad['position'] == 'MID'].head(3)
    selected_forwards = squad[squad['position'] == 'FWD'].head(1)

    best_11 = pd.concat([selected_goalkeepers, selected_defenders, selected_midfielders, selected_forwards])

    # Ensure no duplicate players in the starting 11
    remaining_spots = 11 - len(best_11)
    remaining_players = squad[~squad.index.isin(best_11.index)].sort_values(by=avg_criteria or criteria, ascending=False)

    for i in range(remaining_spots):
        best_11 = pd.concat([best_11, remaining_players.iloc[[i]]])

    # Pick a captain from the best 11 based on the highest criteria or average criteria
    captain = best_11.sort_values(by=avg_criteria or criteria, ascending=False).iloc[0]

    return squad, best_11, captain

# Example usage:
# For GW 1: squad, best_11, captain = pick_best_squad(df[df["GW"] == gw], budget=1000, criteria="ict_index")
# For GW 2-38: squad, best_11, captain = pick_best_squad(df[df["GW"] == gw], budget=1000, criteria="ict_index", avg_criteria="avg_ict_last_3_gw", prev_squad=previous_squad)

import pandas as pd
from load_data import load_latest_data

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


def get_eligible_players_for_gw(gw, merged_gw_df):
    """
    Returns a DataFrame of eligible players for a given game week, loading the latest player data from a local JSON file,
    and using the latest now_cost instead of value in the returned dataframe. It also filters out players from the previous game week
    and adds the 3-week average ICT index calculated from the previous 3 game weeks.

    :param gw: The game week number (e.g., 4)
    :param merged_gw_df: The merged game week DataFrame containing all player data
    :return: DataFrame of eligible players with the 3-week average ICT index and latest now_cost
    """

    # Load the latest player data from the local JSON file
    latest_data = load_latest_data()

    # Ensure that the game week is greater than 1 to calculate averages
    if gw < 2:
        raise ValueError("Game week must be at least 2 or higher to calculate averages.")

    # Filter data up to the previous game week (e.g., for GW 4, filter up to GW 3)
    prev_gw_df = merged_gw_df[merged_gw_df["GW"] < gw]

    # Handle cases where GW is less than 4
    window_size = 3 if gw >= 4 else gw - 1

    # Calculate the rolling average ICT index based on available weeks
    prev_gw_df["avg_3w_ict"] = prev_gw_df.groupby("element")["ict_index"].rolling(window=window_size,
                                                                                  min_periods=1).mean().shift(
        1).reset_index(level=0, drop=True)

    # Filter for the current game week
    current_gw_df = merged_gw_df[merged_gw_df["GW"] == gw - 1]

    # Add the average ICT index from the previous game weeks to the current game week's DataFrame
    current_gw_df = pd.merge(current_gw_df, prev_gw_df[["element", "avg_3w_ict"]], on="element", how="left")

    # Filter out players who did not play in the previous game week
    eligible_df = current_gw_df.dropna(subset=["avg_3w_ict"])

    # Merge in the latest now_cost from the fetched JSON data
    latest_cost_df = pd.DataFrame(latest_data)[["id", "now_cost"]].rename(columns={"id": "element"})
    eligible_df = pd.merge(eligible_df, latest_cost_df, on="element", how="left")

    # Replace the old "value" column with the "now_cost"
    eligible_df["value"] = eligible_df["now_cost"]
    eligible_df.drop(columns=["now_cost"], inplace=True)

    # Print the number of eligible players before returning
    print(f"Number of eligible players: {len(eligible_df)}")

    # Return the DataFrame with all columns along with the calculated average ICT index and updated now_cost as value
    return eligible_df

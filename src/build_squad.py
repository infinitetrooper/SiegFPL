import pandas as pd
import pulp
from x_pts import calculate_expected_points, predict_future_xPts
from load_data import create_current_team_df
pd.set_option('future.no_silent_downcasting', True)

def get_eligible_players_for_gw(gw, merged_gw_df, latest_data=None):
    """
    Returns a DataFrame of eligible players for a given game week, with additional calculations like average 3-week ICT index and expected points (xPts).
    """
    # Ensure required columns are present and appropriately mapped
    required_columns = {'element_type', 'position', 'element', 'xPts'}
    if not required_columns.issubset(merged_gw_df.columns):
        if "element_type" not in merged_gw_df.columns and "position" in merged_gw_df.columns:
            position_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
            merged_gw_df["element_type"] = merged_gw_df["position"].map({v: k for k, v in position_map.items()})

        if "position" not in merged_gw_df.columns and "element_type" in merged_gw_df.columns:
            position_map = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
            merged_gw_df["position"] = merged_gw_df['element_type'].map(position_map)

    if gw < 2:
        raise ValueError("Game week must be at least 2 or higher to calculate averages.")

    # Step 1: Calculate avg_3w_ict ending gw - 1
    prev_gw_df = merged_gw_df[merged_gw_df["GW"] < gw].copy()  # Explicit copy to avoid chained assignment issues
    window_size = 3 if gw >= 4 else gw - 1

    # Step 2: Filter the current game week data
    current_gw_df = merged_gw_df[merged_gw_df["GW"] == gw - 1].copy()

    # Step 3: Calculate the avg_3w_ict
    prev_gw_df["avg_3w_ict"] = prev_gw_df.groupby("element")["ict_index"].rolling(
        window=window_size, min_periods=1
    ).mean().reset_index(level=0, drop=True)

    # Step 4: Filter prev_gw_df to only include rows where both element and GW are in current_gw_df
    filtered_prev_gw_df = prev_gw_df[
        prev_gw_df.set_index(["element", "GW"]).index.isin(current_gw_df.set_index(["element", "GW"]).index)
    ].copy()

    # Step 5: Merge the avg_3w_ict back into the current game week data
    current_gw_df = pd.merge(
        current_gw_df,
        filtered_prev_gw_df[["element", "avg_3w_ict"]],
        on="element",
        how="left"
    )

    # Step 6: Filter out rows where avg_3w_ict is NaN or <= 0
    eligible_df = current_gw_df.dropna(subset=["avg_3w_ict"])
    eligible_df = eligible_df[eligible_df["avg_3w_ict"] > 0].copy()

    if latest_data is not None:
        print("Using latest data in getting eligible players.")
        # Convert latest_data into a DataFrame with relevant columns
        latest_cost_df = pd.DataFrame(latest_data)[["id", "now_cost", "chance_of_playing_next_round"]].rename(
            columns={"id": "element"}
        )

        # Merge eligible_df with latest_cost_df on the element column
        eligible_df = pd.merge(eligible_df, latest_cost_df, on="element", how="left")

        # Fill missing values for "chance_of_playing_next_round" with 100
        eligible_df["chance_of_playing_next_round"] = eligible_df["chance_of_playing_next_round"].fillna(100)

        # Assign the "value" column as "now_cost"
        eligible_df["value"] = eligible_df["now_cost"]


    # Step 7: Add xPts for these players
    position_coefficients = calculate_expected_points()
    eligible_df["xPts"] = eligible_df.apply(
        lambda row: round(predict_future_xPts(row["avg_3w_ict"], row["position"], position_coefficients), 2), axis=1
    )

    return eligible_df

def pick_best_squad(player_data, budget=1000, criteria="xPts", prev_squad=None, free_transfers=1, transfer_threshold=4):
    """
    Picks the best squad if there is no previous squad. If a previous squad exists, it suggests transfers to improve the squad.
    Returns the full squad, best 11 players, and the captain.
    """
    position_col = 'position' if 'position' in player_data.columns else 'element_type'
    if position_col == 'element_type':
        player_data['position'] = player_data['element_type'].map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})

    cost_column = "now_cost" if "now_cost" in player_data.columns else "value"
    player_data = player_data.sort_values(by=criteria, ascending=False)

    if prev_squad is None:
        # Pick a new squad
        # squad = select_new_squad(player_data, budget, cost_column, criteria)
        squad = select_best_squad_ilp(player_data, budget, cost_column, criteria)
    else:
        # Use the handle_transfers function to update the squad
        current_team = create_current_team_df(picks_df=prev_squad, player_data=player_data)
        squad = handle_transfers(current_team, player_data, free_transfers, transfer_threshold, criteria)

    # Ensure squad is not None before proceeding
    if squad is None or squad.empty:
        raise ValueError("Failed to generate a valid squad. Please check the input data.")

    best_11 = select_best_11(squad, criteria)
    captain = choose_captain(best_11, criteria)
    return squad, best_11, captain

def select_best_squad_ilp(player_data, budget, cost_column, criteria):
    # Define the problem
    prob = pulp.LpProblem("Squad_Selection", pulp.LpMaximize)

    # Decision variables
    player_vars = pulp.LpVariable.dicts("player", player_data.index, cat='Binary')

    # Objective function: Maximize total xPts
    prob += pulp.lpSum([player_data.loc[i, criteria] * player_vars[i] for i in player_data.index])

    # Constraint: Total cost should be less than or equal to budget
    prob += pulp.lpSum([player_data.loc[i, cost_column] * player_vars[i] for i in player_data.index]) <= budget

    # Constraints: Position requirements
    position_limits = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
    for position, limit in position_limits.items():
        prob += pulp.lpSum([player_vars[i] for i in player_data.index if player_data.loc[i, 'position'] == position]) == limit

    # Constraint: Maximum of 3 players from the same team
    for team in player_data['team'].unique():
        prob += pulp.lpSum([player_vars[i] for i in player_data.index if player_data.loc[i, 'team'] == team]) <= 3

    # Solve the problem with suppressed output
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # Print the status of the solution
    print("Status:", pulp.LpStatus[prob.status])

    # Extract the selected players
    selected_players = [i for i in player_data.index if player_vars[i].varValue == 1]
    squad = player_data.loc[selected_players]

    return squad

def handle_transfers(current_team: pd.DataFrame, eligible_players: pd.DataFrame, free_transfers: int,
                     transfer_threshold: int, criteria: str = "xPts") -> pd.DataFrame:
    """
    Handles transfers to improve the current team based on xPts criteria.
    1. For each position, find the lowest xPts player.
    2. Search for a replacement within the budget that has higher xPts.
    3. Sort these potential replacements by xPts difference.
    4. Replace the player with the highest xPts difference.
    Args:
        current_team (pd.DataFrame): DataFrame containing the current team data.
        eligible_players (pd.DataFrame): DataFrame containing eligible players for the gameweek.
        free_transfers (int): Number of free transfers available.
        transfer_threshold (int): The minimum xPts improvement required to justify a paid transfer.
        criteria (str): The criteria to base the transfers on, typically "xPts".
    Returns:
        pd.DataFrame: Updated team after making transfers.
    """
    # Validate input DataFrames
    required_columns = {'position', criteria, 'element', 'element_type'}
    assert required_columns.issubset(
        current_team.columns), f"current_team is missing required columns: {required_columns - set(current_team.columns)}"
    assert required_columns.issubset(
        eligible_players.columns), f"eligible_players is missing required columns: {required_columns - set(eligible_players.columns)}"

    # Define cost and name columns for current_team
    current_team_cost_column = "now_cost" if "now_cost" in current_team.columns else "value"
    current_team_name_column = "web_name" if "web_name" in current_team.columns else "name"
    # Define cost and name columns for eligible_players
    eligible_players_cost_column = "now_cost" if "now_cost" in eligible_players.columns else "value"
    eligible_players_name_column = "web_name" if "web_name" in eligible_players.columns else "name"

    # Ensure the 'position' column is correctly assigned using 'element_type'
    position_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    current_team['position'] = current_team.get('position', current_team['element_type'].map(position_map))
    eligible_players['position'] = eligible_players.get('position', eligible_players['element_type'].map(position_map))

    # Treat NaN values in the criteria column as 0
    current_team[criteria] = current_team[criteria].fillna(0).infer_objects(copy=False)
    eligible_players[criteria] = eligible_players[criteria].fillna(0).infer_objects(copy=False)

    print(f"Total squad cost before transfers: {current_team[current_team_cost_column].sum()}")
    max_budget = max(current_team[current_team_cost_column].sum(), 1000)  # Maximum budget for the squad

    # Store possible transfers (player_out, player_in, xPts_difference)
    potential_transfers = []

    # Initialize a set to keep track of used replacements
    used_replacements = set()

    # Sort the current team by the criteria (e.g., xPts) in ascending order
    current_team_sorted = current_team.sort_values(by=criteria, ascending=True)

    # Iterate over each player in the sorted current team
    for _, player in current_team_sorted.iterrows():
        filtered_replacements = eligible_players[
            (eligible_players['position'] == player['position']) &  # Same position
            (eligible_players[criteria] > player[criteria])  # Higher xPts
            & (~eligible_players['element'].isin([player['element']]))  # Exclude the player itself
            # & (eligible_players['team'].isin(current_team['team'].value_counts()[current_team['team'].value_counts() < 3].index))  # Check club limit
            ].sort_values(by=criteria, ascending=False)

        print("Filtered replacements for: ", player[current_team_name_column], "are", filtered_replacements.shape[0])
        # Iterate over each eligible player to find potential replacements
        for _, replacement in filtered_replacements.iterrows():
            updated_squad_cost = current_team[current_team_cost_column].sum() - player[current_team_cost_column] + \
                                 replacement[eligible_players_cost_column]
            if (replacement['element'] not in used_replacements and updated_squad_cost <= max_budget):
                xPts_difference = replacement[criteria] - player[criteria]
                potential_transfers.append((player, replacement, xPts_difference))
                used_replacements.add(replacement['element'])
                break

    # Sort the potential replacements by xPts difference in descending order
    potential_transfers.sort(key=lambda x: x[2], reverse=True)

    # Perform free transfers first
    transfers_made = 0
    for transfer in potential_transfers[:free_transfers]:
        player_out, player_in, _ = transfer
        current_team = current_team[current_team['element'] != player_out['element']]  # Remove old player
        current_team = pd.concat([current_team, player_in.to_frame().T])  # Add new player
        print("Transferred: ", player_out['name'], "with", player_in['name'])
        transfers_made += 1

    # Perform additional transfers if xPts improvement is greater than the transfer threshold
    for transfer in potential_transfers[free_transfers:]:
        player_out, player_in, xPts_difference = transfer
        if xPts_difference > transfer_threshold:
            current_team = current_team[current_team['element'] != player_out['element']]  # Remove old player
            current_team = pd.concat([current_team, player_in.to_frame().T])  # Add new player
            print("Transferred: ", player_out['name'], "with", player_in['name'])
            transfers_made += 1

    print(f"\nTotal transfers made: {transfers_made}")
    print(f"Total squad cost after transfers: {current_team[current_team_cost_column].sum()}")

    # Ensure squad still has 15 players
    if len(current_team) != 15:
        raise ValueError("Squad size must be 15 players after transfers.")

    return current_team

def select_best_11(squad, criteria="xPts"):
    """
    Selects the best 11 players from the squad, ensuring position constraints are met, including limiting to 1 goalkeeper.
    """
    best_11 = pd.concat([
        squad[squad['position'] == 'GK'].sort_values(by=criteria, ascending=False).head(1),
        squad[squad['position'] == 'DEF'].sort_values(by=criteria, ascending=False).head(3),
        squad[squad['position'] == 'MID'].sort_values(by=criteria, ascending=False).head(3),
        squad[squad['position'] == 'FWD'].sort_values(by=criteria, ascending=False).head(1)
    ])

    remaining_spots = 11 - len(best_11)
    additional_players = squad[~squad.index.isin(best_11.index)].sort_values(by=criteria, ascending=False)

    # Fill the remaining spots, ensuring no more than 1 goalkeeper
    for _, player in additional_players.iterrows():
        if remaining_spots == 0:
            break
        # Add the player only if it's not a goalkeeper (GK) or if we already have 1 GK in best 11
        if player['position'] != 'GK' or best_11[best_11['position'] == 'GK'].shape[0] == 1:
            # Before concatenating, drop any columns that are all NaN from the player DataFrame
            player_df = player.to_frame().T.dropna(axis=1, how='all')

            # Then, concatenate the player DataFrame with best_11
            best_11 = pd.concat([best_11, player_df])
            remaining_spots -= 1

    return best_11

def choose_captain(best_11, criteria="xPts"):
    """
    Chooses the captain based on the highest criteria in the best 11 players.
    """
    captain = best_11.sort_values(by=criteria, ascending=False).iloc[0]
    return captain



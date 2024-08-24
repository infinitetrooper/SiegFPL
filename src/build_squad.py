import pandas as pd
from x_pts import calculate_expected_points, predict_future_xPts
from load_data import load_latest_data, create_current_team_df

# Function to get eligible players for a given game week
def get_eligible_players_for_gw(gw, merged_gw_df):
    latest_data = load_latest_data()

    if gw < 2:
        raise ValueError("Game week must be at least 2 or higher to calculate averages.")

    # Filter data up to the previous game week (e.g., for GW 4, filter up to GW 3)
    prev_gw_df = merged_gw_df[merged_gw_df["GW"] < gw]

    # Handle cases where GW is less than 4
    window_size = 3 if gw >= 4 else gw - 1

    # Calculate the rolling average ICT index correctly by grouping by 'element' first
    prev_gw_df["avg_3w_ict"] = prev_gw_df.groupby("element")["ict_index"].rolling(window=window_size, min_periods=1).mean().reset_index(level=0, drop=True)

    # Filter for the current game week
    current_gw_df = merged_gw_df[merged_gw_df["GW"] == gw - 1]

    # Merge the 3-week average ICT index into the current game week’s data
    current_gw_df = pd.merge(current_gw_df, prev_gw_df[["element", "avg_3w_ict"]], on="element", how="left")

    # Filter out players who did not play in the previous game week
    eligible_df = current_gw_df.dropna(subset=["avg_3w_ict"])

    # Merge in the latest now_cost and chance_of_playing_next_round from the fetched JSON data
    latest_cost_df = pd.DataFrame(latest_data)[["id", "now_cost", "chance_of_playing_next_round"]].rename(columns={"id": "element"})
    eligible_df = pd.merge(eligible_df, latest_cost_df, on="element", how="left")

    eligible_df["chance_of_playing_next_round"] = eligible_df["chance_of_playing_next_round"].fillna(100)
    eligible_df["value"] = eligible_df["now_cost"]
    eligible_df.drop(columns=["now_cost"], inplace=True)

    # Get coefficients and intercept using the existing calculate_expected_points function
    coef, intercept = calculate_expected_points()

    # Calculate xPts using the predict_future_xPts function and avg_3w_ict, then round the result
    eligible_df["xPts"] = eligible_df["avg_3w_ict"].apply(lambda x: round(predict_future_xPts(x, coef, intercept), 2))

    print(f"Number of eligible players: {len(eligible_df)}")

    return eligible_df

def handle_transfers(current_team, player_data, free_transfers, transfer_penalty, criteria="xPts", xPts_threshold=4):
    """
    Suggests transfers to improve an existing team based on given criteria.

    Args:
        current_team (pd.DataFrame): The current team data.
        player_data (pd.DataFrame): The player data for the specific game week.
        free_transfers (int): Number of free transfers available.
        transfer_penalty (int): Penalty for additional transfers beyond the free transfers.
        criteria (str): The criteria used to select replacements (default is "xPts").
        xPts_threshold (int): The minimum xPts difference needed to justify an additional transfer.

    Returns:
        pd.DataFrame: The updated team after transfers.
    """
    # Use "now_cost" if "value" does not exist
    cost_column = "now_cost" if "now_cost" in player_data.columns else "value"

    # Determine the column to use for player names (fall back to 'name' if 'web_name' is not available)
    name_column = "web_name" if "web_name" in player_data.columns else "name"

    player_data = player_data.sort_values(by=criteria, ascending=False)

    initial_cost = current_team[cost_column].sum()
    total_transfers = 0
    transfers = []

    # First round: Make transfers using free transfers to improve the team
    for _, player in current_team.iterrows():
        potential_replacements = player_data[(player_data['position'] == player['position']) &
                                             (~player_data.index.isin(current_team.index)) &
                                             (player_data[cost_column] <= player[cost_column])]

        if not potential_replacements.empty:
            best_replacement = potential_replacements.sort_values(by=criteria, ascending=False).iloc[0]
            if best_replacement[criteria] > player[criteria]:
                transfers.append((player[name_column], best_replacement[name_column]))
                current_team = current_team.drop(player.name)
                current_team = pd.concat([current_team, best_replacement.to_frame().T])
                total_transfers += 1

                # Stop if we've exhausted the free transfers
                if total_transfers >= free_transfers:
                    break

    # Second round: Make additional transfers only if xPts improvement is above the threshold
    for _, player in current_team.iterrows():
        potential_replacements = player_data[(player_data['position'] == player['position']) &
                                             (~player_data.index.isin(current_team.index)) &
                                             (player_data[cost_column] <= player[cost_column])]

        if not potential_replacements.empty:
            best_replacement = potential_replacements.sort_values(by=criteria, ascending=False).iloc[0]
            xPts_difference = best_replacement[criteria] - player[criteria]

            if xPts_difference > xPts_threshold:
                transfers.append((player[name_column], best_replacement[name_column]))
                current_team = current_team.drop(player.name)
                current_team = pd.concat([current_team, best_replacement.to_frame().T])
                total_transfers += 1

    # Calculate the transfer penalty if transfers exceed free transfers
    if total_transfers > free_transfers:
        total_penalty = (total_transfers - free_transfers) * transfer_penalty
    else:
        total_penalty = 0

    # Ensure the final squad cost does not exceed the initial budget
    while current_team[cost_column].sum() > initial_cost:
        lowest_xPts_player = current_team.sort_values(by=criteria).iloc[0]
        current_team = current_team.drop(lowest_xPts_player.name)

    print(f"Total transfers made: {total_transfers}, Transfer penalty: {total_penalty} points")

    return current_team

def pick_best_squad(player_data: pd.DataFrame, budget=1000, criteria="xPts", prev_squad=None, free_transfers=1, transfer_penalty=4):
    """
    Picks the best squad if there is no previous squad. If a previous squad exists, it suggests transfers to improve the squad.
    Always returns the full squad, best 11 players, and the captain.

    Args:
        player_data (pd.DataFrame): The player data for the specific game week.
        budget (int): The budget for the squad (default is 1000).
        criteria (str): The criteria used to sort and select players (default is "xPts").
        prev_squad (pd.DataFrame): The previous squad (if available).
        free_transfers (int): Number of free transfers available.
        transfer_penalty (int): Penalty for additional transfers beyond the free transfers.

    Returns:
        pd.DataFrame, pd.DataFrame, pd.Series: The selected squad, best 11 players, and the captain.
    """
    position_col = 'position' if 'position' in player_data.columns else 'element_type'
    if position_col == 'element_type':
        player_data['position'] = player_data['element_type'].map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})

    # Use "now_cost" if "value" does not exist
    cost_column = "now_cost" if "now_cost" in player_data.columns else "value"
    player_data = player_data.sort_values(by=criteria, ascending=False)

    if prev_squad is None:
        # Pick the best squad (new squad)
        selected_goalkeepers = []
        selected_defenders = []
        selected_midfielders = []
        selected_forwards = []

        remaining_budget = budget

        position_limits = {
            'GK': 2,
            'DEF': 5,
            'MID': 5,
            'FWD': 3
        }

        for position, limit in position_limits.items():
            position_players = player_data[player_data['position'] == position]

            for _, player in position_players.iterrows():
                if position == 'GK' and len(selected_goalkeepers) < limit and player[cost_column] <= remaining_budget:
                    selected_goalkeepers.append(player)
                    remaining_budget -= player[cost_column]
                elif position == 'DEF' and len(selected_defenders) < limit and player[cost_column] <= remaining_budget:
                    selected_defenders.append(player)
                    remaining_budget -= player[cost_column]
                elif position == 'MID' and len(selected_midfielders) < limit and player[cost_column] <= remaining_budget:
                    selected_midfielders.append(player)
                    remaining_budget -= player[cost_column]
                elif position == 'FWD' and len(selected_forwards) < limit and player[cost_column] <= remaining_budget:
                    selected_forwards.append(player)
                    remaining_budget -= player[cost_column]

        squad = pd.DataFrame(selected_goalkeepers + selected_defenders + selected_midfielders + selected_forwards)

        # Ensure the squad is within the budget
        while squad[cost_column].sum() > budget:
            lowest_xPts_player = squad.sort_values(by=criteria).iloc[0]
            position = lowest_xPts_player['position']
            replacements = player_data[(player_data['position'] == position) &
                                       (~player_data.index.isin(squad.index)) &
                                       (player_data[cost_column] < lowest_xPts_player[cost_column])]

            if not replacements.empty:
                replacement = replacements.sort_values(by=criteria, ascending=False).iloc[0]
                squad = squad.drop(lowest_xPts_player.name)
                squad = pd.concat([squad, replacement.to_frame().T])
            else:
                break

    else:
        # Use the handle_transfers function to update the squad
        current_team = create_current_team_df(picks_df=prev_squad, player_data=player_data)
        squad = handle_transfers(current_team, player_data, free_transfers, transfer_penalty, criteria)

    # Select the best 11 players
    best_11 = pd.concat([
        squad[squad['position'] == 'GK'].head(1),
        squad[squad['position'] == 'DEF'].head(3),
        squad[squad['position'] == 'MID'].head(3),
        squad[squad['position'] == 'FWD'].head(1)
    ])

    remaining_spots = 11 - len(best_11)
    best_11 = pd.concat([best_11, squad[~squad.index.isin(best_11.index)].sort_values(by=criteria, ascending=False).head(remaining_spots)])

    # Pick a captain from the best 11 based on the highest criteria
    captain = best_11.sort_values(by=criteria, ascending=False).iloc[0]

    return squad, best_11, captain

def calculate_total_expected_points(current_team_df):
    """
    Calculates the total expected points (xPts) for the current team, considering the multiplier for captains and vice-captains.

    Args:
        current_team_df (pd.DataFrame): The current team DataFrame with columns including 'xPts' and 'multiplier'.

    Returns:
        float: The total expected points for the current team.
    """
    # Ensure that the 'xPts' and 'multiplier' columns are present in the DataFrame
    if 'xPts' not in current_team_df.columns or 'multiplier' not in current_team_df.columns:
        raise ValueError("The DataFrame must include 'xPts' and 'multiplier' columns.")

    # Calculate the total expected points considering the multipliers
    total_expected_points = (current_team_df['xPts'] * current_team_df['multiplier']).sum()

    return total_expected_points

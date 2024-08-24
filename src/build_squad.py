import pandas as pd
from x_pts import calculate_expected_points, predict_future_xPts
from load_data import load_latest_data

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

# Function to pick the best squad
def pick_best_squad(player_data: pd.DataFrame, budget=1000, criteria="avg_3w_ict") -> (pd.DataFrame, pd.DataFrame, pd.Series):
    position_col = 'position' if 'position' in player_data.columns else 'element_type'
    if position_col == 'element_type':
        player_data['position'] = player_data['element_type'].map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})

    cost_column = 'now_cost' if 'now_cost' in player_data.columns else 'value'
    player_data = player_data.sort_values(by=criteria, ascending=False)

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

    best_11 = pd.concat([
        squad[squad['position'] == 'GK'].head(1),
        squad[squad['position'] == 'DEF'].head(3),
        squad[squad['position'] == 'MID'].head(3),
        squad[squad['position'] == 'FWD'].head(1)
    ])

    remaining_spots = 11 - len(best_11)
    best_11 = pd.concat([best_11, squad[~squad.index.isin(best_11.index)].sort_values(by=criteria, ascending=False).head(remaining_spots)])

    captain = best_11.sort_values(by=criteria, ascending=False).iloc[0]

    return squad, best_11, captain

# Function to suggest transfers to improve an existing team
def suggest_transfers(current_team: pd.DataFrame, player_data: pd.DataFrame, free_transfers: int, transfer_penalty: int, criteria="xPts") -> pd.DataFrame:
    cost_column = 'now_cost'
    player_data = player_data.sort_values(by=criteria, ascending=False)

    initial_cost = current_team[cost_column].sum()
    total_transfers = 0
    transfers = []

    for _, player in current_team.iterrows():
        potential_replacements = player_data[(player_data['position'] == player['position']) &
                                             (~player_data.index.isin(current_team.index)) &
                                             (player_data[cost_column] <= player[cost_column])]

        if not potential_replacements.empty:
            best_replacement = potential_replacements.sort_values(by=criteria, ascending=False).iloc[0]
            if best_replacement[criteria] > player[criteria]:
                transfers.append((player['name'], best_replacement['name']))
                current_team = current_team.drop(player.name)
                current_team = pd.concat([current_team, best_replacement.to_frame().T])
                total_transfers += 1

    if total_transfers > free_transfers:
        total_penalty = (total_transfers - free_transfers) * transfer_penalty
    else:
        total_penalty = 0

    if current_team[cost_column].sum() > initial_cost:
        rollback_needed = current_team[cost_column].sum() - initial_cost
        for i, (old_player, new_player) in enumerate(transfers[::-1]):
            old_player_data = player_data[(player_data['name'] == old_player) & (player_data['position'] == current_team.loc[current_team['name'] == new_player, 'position'].values[0])]
            if not old_player_data.empty and rollback_needed >= (new_player[cost_column] - old_player_data[cost_column]).values[0]:
                rollback_needed -= (new_player[cost_column] - old_player_data[cost_column]).values[0]
                current_team = current_team.drop(new_player.name)
                current_team = pd.concat([current_team, old_player_data])

    final_xPts = current_team['xPts'].sum() - total_penalty

    print(f"Total transfers made: {total_transfers}, Transfer penalty: {total_penalty} points, Final xPts: {final_xPts}")

    return current_team
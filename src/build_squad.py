import pandas as pd
from x_pts import calculate_expected_points, predict_future_xPts
from load_data import load_latest_data, create_current_team_df


def get_eligible_players_for_gw(gw, merged_gw_df, latest_data=load_latest_data()):
    """
    Returns a DataFrame of eligible players for a given game week, with additional calculations like average 3-week ICT index and expected points (xPts).
    """
    if gw < 2:
        raise ValueError("Game week must be at least 2 or higher to calculate averages.")

    prev_gw_df = merged_gw_df[merged_gw_df["GW"] < gw]
    window_size = 3 if gw >= 4 else gw - 1

    prev_gw_df["avg_3w_ict"] = prev_gw_df.groupby("element")["ict_index"].rolling(window=window_size,
                                                                                  min_periods=1).mean().reset_index(
        level=0, drop=True)

    current_gw_df = merged_gw_df[merged_gw_df["GW"] == gw - 1]
    current_gw_df = pd.merge(current_gw_df, prev_gw_df[["element", "avg_3w_ict"]], on="element", how="left")
    eligible_df = current_gw_df.dropna(subset=["avg_3w_ict"])

    latest_cost_df = pd.DataFrame(latest_data)[["id", "now_cost", "chance_of_playing_next_round"]].rename(
        columns={"id": "element"})
    eligible_df = pd.merge(eligible_df, latest_cost_df, on="element", how="left")

    eligible_df["chance_of_playing_next_round"] = eligible_df["chance_of_playing_next_round"].fillna(100)
    eligible_df["value"] = eligible_df["now_cost"]
    eligible_df.drop(columns=["now_cost"], inplace=True)

    # Calculate position-based coefficients and intercepts
    position_coefficients = calculate_expected_points()

    # Calculate xPts for each player based on their position and 3-week average ICT index
    eligible_df["xPts"] = eligible_df.apply(
        lambda row: round(predict_future_xPts(row["avg_3w_ict"], row["position"], position_coefficients), 2), axis=1
    )

    print(f"Number of eligible players: {len(eligible_df)}")
    return eligible_df

def pick_best_squad(player_data, budget=1000, criteria="xPts", prev_squad=None, free_transfers=1, transfer_penalty=4):
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
        squad = select_new_squad(player_data, budget, cost_column, criteria)
    else:
        # Use the handle_transfers function to update the squad
        current_team = create_current_team_df(picks_df=prev_squad, player_data=player_data)
        squad = handle_transfers(player_data, current_team, free_transfers, transfer_penalty, criteria)

    # Ensure squad is not None before proceeding
    if squad is None or squad.empty:
        raise ValueError("Failed to generate a valid squad. Please check the input data.")

    best_11 = select_best_11(squad, criteria)
    captain = choose_captain(best_11, criteria)
    return squad, best_11, captain

def select_new_squad(player_data, budget, cost_column, criteria):
    """
    Selects a new squad within the given budget.
    """
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

    return squad if not squad.empty else None

def handle_transfers(player_data, prev_squad, free_transfers, transfer_penalty, criteria="xPts", xPts_threshold=4):
    """
    Suggests transfers to improve an existing team based on given criteria.
    """
    cost_column = "now_cost" if "now_cost" in player_data.columns else "value"
    name_column = "web_name" if "web_name" in player_data.columns else "name"

    player_data = player_data.sort_values(by=criteria, ascending=False)
    initial_cost = max(1000, prev_squad[cost_column].sum())
    total_transfers = 0
    transfers = []

    # First round: Make transfers using free transfers to improve the team
    for _, player in prev_squad.iterrows():
        potential_replacements = player_data[(player_data['position'] == player['position']) &
                                             (~player_data.index.isin(prev_squad.index)) &
                                             (player_data[cost_column] <= player[cost_column])]

        if not potential_replacements.empty:
            best_replacement = potential_replacements.sort_values(by=criteria, ascending=False).iloc[0]
            if best_replacement[criteria] > player[criteria]:
                transfers.append((player[name_column], best_replacement[name_column]))
                prev_squad = prev_squad.drop(player.name)
                prev_squad = pd.concat([prev_squad, best_replacement.to_frame().T])
                total_transfers += 1

                if total_transfers >= free_transfers:
                    break

    # Second round: Make additional transfers only if xPts improvement is above the threshold
    for _, player in prev_squad.iterrows():
        potential_replacements = player_data[(player_data['position'] == player['position']) &
                                             (~player_data.index.isin(prev_squad.index)) &
                                             (player_data[cost_column] <= player[cost_column])]

        if not potential_replacements.empty:
            best_replacement = potential_replacements.sort_values(by=criteria, ascending=False).iloc[0]
            xPts_difference = best_replacement[criteria] - player[criteria]

            if xPts_difference > xPts_threshold:
                transfers.append((player[name_column], best_replacement[name_column]))
                prev_squad = prev_squad.drop(player.name)
                prev_squad = pd.concat([prev_squad, best_replacement.to_frame().T])
                total_transfers += 1

    if total_transfers > free_transfers:
        total_penalty = (total_transfers - free_transfers) * transfer_penalty
    else:
        total_penalty = 0

    while prev_squad[cost_column].sum() > initial_cost:
        lowest_xPts_player = prev_squad.sort_values(by=criteria).iloc[0]
        prev_squad = prev_squad.drop(lowest_xPts_player.name)

    print(f"Total transfers made: {total_transfers}, Transfer penalty: {total_penalty} points")
    return prev_squad

def select_best_11(squad, criteria="xPts"):
    """
    Selects the best 11 players from the squad, ensuring position constraints are met, including limiting to 1 goalkeeper.
    """
    # Select the best 1 goalkeeper for the starting 11
    best_11 = pd.concat([
        squad[squad['position'] == 'GK'].head(1),
        squad[squad['position'] == 'DEF'].head(3),
        squad[squad['position'] == 'MID'].head(3),
        squad[squad['position'] == 'FWD'].head(1)
    ])

    remaining_spots = 11 - len(best_11)
    additional_players = squad[~squad.index.isin(best_11.index)].sort_values(by=criteria, ascending=False)

    # Fill the remaining spots, ensuring no more than 1 goalkeeper
    for _, player in additional_players.iterrows():
        if remaining_spots == 0:
            break
        # Add the player only if it's not a goalkeeper (GK) or if we already have 1 GK in best 11
        if player['position'] != 'GK':
            best_11 = pd.concat([best_11, player.to_frame().T])
            remaining_spots -= 1

    return best_11

def choose_captain(best_11, criteria="xPts"):
    """
    Chooses the captain based on the highest criteria in the best 11 players.
    """
    captain = best_11.sort_values(by=criteria, ascending=False).iloc[0]
    return captain



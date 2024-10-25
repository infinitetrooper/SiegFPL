import pandas as pd
import pulp
import numpy as np
from src.x_pts import calculate_expected_points, predict_future_xPts
from src.load_data import create_current_team_df, load_fixture_data
from src.fixture_difficulty import scale_pts_by_difficulty
pd.set_option('future.no_silent_downcasting', True)

def get_eligible_players_for_gw(gw, merged_gw_df, latest_data=None):
    """
    Returns a DataFrame of eligible players for a given game week, with additional calculations like average 3-week ICT index and expected points (xPts).
    """
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


    # Find the latest available gameweek in the data
    max_available_gw = merged_gw_df["GW"].max()
    target_gw = min(gw - 1, max_available_gw)
    # Calculate how many previous gameweeks we can use
    available_gws = merged_gw_df[merged_gw_df["GW"] <= target_gw]["GW"].unique()
    window_size = min(3, len(available_gws))  # Use what's available up to 3 weeks

    # Step 1: Calculate avg_3w_ict ending gw - 1
    prev_gw_df = merged_gw_df[merged_gw_df["GW"] <= target_gw].copy()
    
    # Step 2: Filter the current game week data
    current_gw_df = prev_gw_df.loc[prev_gw_df.groupby("element")["GW"].idxmax()].copy()

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
        # Convert latest_data into a DataFrame with relevant columns
        latest_cost_df = pd.DataFrame(latest_data)[["id", "now_cost", "chance_of_playing_next_round", "web_name"]].rename(columns={"id": "element"})

        # Merge eligible_df with latest_cost_df on the element column
        eligible_df = pd.merge(eligible_df, latest_cost_df, on="element", how="left", indicator=False)

        # Fill missing values for "chance_of_playing_next_round" with 100
        eligible_df["chance_of_playing_next_round"] = eligible_df["chance_of_playing_next_round"].fillna(100)

        # Assign the "value" column as "now_cost"
        eligible_df["value"] = eligible_df["now_cost"]

    fixtures = load_fixture_data(year="2024-25")

    eligible_df = pd.merge(eligible_df, fixtures, on=['GW', 'fixture'], how="left")
    eligible_df['player_team'] = eligible_df.apply(lambda row: row['team_h'] if row['was_home'] == 1 else row['team_a'], axis=1)

    gw_fixtures = fixtures[fixtures['GW'] == gw]
    
    home_df = pd.merge(
        eligible_df,
        gw_fixtures,
        left_on="player_team",
        right_on=["team_h"],
        suffixes=("", "_next")
    )

    away_df = pd.merge(
        eligible_df,
        gw_fixtures,
        left_on="player_team",
        right_on=["team_a"],
        suffixes=("", "_next")
    )

    eligible_df = pd.concat([home_df, away_df], ignore_index=True)

    eligible_df['difficulty'] = eligible_df.apply(
        lambda row: row['team_h_difficulty_next'] if row['player_team'] == row['team_h_next'] else row['team_a_difficulty_next'], axis=1)

    # Step 7: Add xPts for these players
    position_coefficients = calculate_expected_points()
    difficulty_factors = scale_pts_by_difficulty()
    
    # Merge scale_factor based on position and difficulty into eligible_df
    eligible_df = pd.merge(
        eligible_df,
        difficulty_factors,
        on=["position", "difficulty"],
        how="left"
    )

    eligible_df["xPts"] = eligible_df.apply(
        lambda row: round(
            predict_future_xPts(row["avg_3w_ict"], row["position"], position_coefficients, row["scale_factor"]),
            2),
        axis=1
    )

    return eligible_df


def pick_best_squad(player_data, budget=1000, criteria="xPts", prev_squad=None, free_transfers=1, transfer_threshold=4):
    """
    Picks the best squad if there is no previous squad. If a previous squad exists, it suggests transfers to improve the squad.
    Returns the full squad, best 11 players, the captain, and the transfers made.
    """
    position_col = 'position' if 'position' in player_data.columns else 'element_type'
    if position_col == 'element_type':
        player_data['position'] = player_data['element_type'].map({1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'})

    cost_column = "now_cost" if "now_cost" in player_data.columns else "value"
    player_data = player_data.sort_values(by=criteria, ascending=False)

    transfers = []  # Initialize transfers list

    if prev_squad is None:
        # Pick a new squad
        squad = select_best_squad_ilp(player_data, budget, cost_column, criteria)
    else:
        # Use the handle_transfers function to update the squad
        current_team = create_current_team_df(picks_df=prev_squad, player_data=player_data)
        squad, transfers = optimize_transfers(current_team, player_data, free_transfers, budget, transfer_penalty=transfer_threshold)

    # Ensure squad is not None before proceeding
    if squad is None or squad.empty:
        raise ValueError("Failed to generate a valid squad. Please check the input data.")

    best_11 = select_best_11(squad, criteria)
    captain = choose_captain(best_11, criteria)
    return squad, best_11, captain, transfers

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

def optimize_transfers(current_team, eligible_players, free_transfers, value, criteria="xPts", transfer_penalty=4):
    """
    Determine the optimal set of transfers to maximize points gain while considering transfer penalties, budget constraints,
    and team (club) constraints.

    Args:
        current_team (pd.DataFrame): DataFrame containing the current team data.
        eligible_players (pd.DataFrame): DataFrame containing eligible players for the gameweek.
        free_transfers (int): Number of free transfers available.
        transfer_penalty (int): Penalty points for each transfer over the free transfers limit.
        criteria (str): The criteria to base the transfers on, typically "xPts".

    Returns:
        pd.DataFrame: Updated squad DataFrame after making optimal transfers.
    """

    # Define cost and name columns for current_team and eligible_players
    current_team_cost_column = "now_cost" if "now_cost" in current_team.columns else "value"
    eligible_players_cost_column = "now_cost" if "now_cost" in eligible_players.columns else "value"

    # Define the team column
    team_column = "team"

    # Estimating potential transfers
    potential_transfers = []
    for _, player_out in current_team.iterrows():
        possible_replacements = eligible_players[
            (eligible_players['position'] == player_out['position']) & 
            (eligible_players[criteria] > player_out[criteria]) & 
            (~eligible_players['element'].isin(current_team['element']))
        ]

        for _, player_in in possible_replacements.iterrows():
            net_points_gain = player_in[criteria] - player_out[criteria]
            potential_transfers.append((player_out, player_in, net_points_gain))

    # Sort potential transfers by net_points_gain in descending order
    potential_transfers = sorted(potential_transfers, key=lambda x: x[2], reverse=True)

    # Calculate the current squad cost and set the maximum budget
    print(f"Current Squad Cost: {value}")

    # Knapsack algorithm to maximize points gain considering transfer penalties and budget constraints
    n = len(potential_transfers)
    dp = np.zeros((n + 1, 2 * free_transfers + 1))
    budget_used = np.zeros((n + 1, 2 * free_transfers + 1))

    # Track the number of players from each team in the squad
    team_counts = current_team[team_column].value_counts().to_dict()

    for i in range(1, n + 1):
        player_out, player_in, point_gain = potential_transfers[i - 1]
        transfer_cost = 1  # One transfer used
        for j in range(2 * free_transfers + 1):
            if j >= transfer_cost:
                new_team_count = team_counts.get(player_in[team_column], 0) + 1
                if new_team_count <= 3:
                    if dp[i][j] < dp[i - 1][j - transfer_cost] + point_gain - (j - free_transfers) * transfer_penalty:
                        dp[i][j] = dp[i - 1][j - transfer_cost] + point_gain - (j - free_transfers) * transfer_penalty
                        budget_used[i][j] = budget_used[i - 1][j - transfer_cost] + player_in[eligible_players_cost_column] - player_out[current_team_cost_column]
            else:
                dp[i][j] = dp[i - 1][j]
                budget_used[i][j] = budget_used[i - 1][j]

    # Traceback to find optimal transfers
    optimal_transfers = []
    w = 2 * free_transfers
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            player_out, player_in, _ = potential_transfers[i - 1]
            optimal_transfers.append((player_out, player_in))
            w -= 1

    # Remove duplicate entries in optimal_transfers without converting to a dictionary
    seen_players = set()
    unique_transfers = []
    for player_out, player_in in optimal_transfers:
        if player_out['element'] not in seen_players:
            unique_transfers.append((player_out, player_in))
            seen_players.add(player_out['element'])
    optimal_transfers = unique_transfers

    # Ensure final budget after all transfers is within the max budget
    final_cost = value
    for player_out, player_in in optimal_transfers:
        final_cost = final_cost - player_out[current_team_cost_column] + player_in[eligible_players_cost_column]

    if final_cost <= value:
        # Update the current team with the optimal transfers
        for player_out, player_in in optimal_transfers:
            print(f"Transfer {player_out['name']} to {player_in['name']}")
            current_team = current_team[current_team['element'] != player_out['element']]  # Remove old player
            current_team = pd.concat([current_team, player_in.to_frame().T])  # Add new player
    else:
        print("No valid transfers found within the budget constraint.")
        optimal_transfers = []

    print(f"Final Squad Cost: {current_team[current_team_cost_column].sum()}")

    return current_team, optimal_transfers

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

import os
import pandas as pd
from datetime import datetime
from get_repo import clone_fpl_repo  # Import the clone function

def load_and_filter_data(year="2023-24", min_gw=10, min_minutes=60):
    """
    Loads the CSV file, filters out players who played fewer than the specified minutes in the specified number of game weeks, and returns the filtered DataFrame.

    :param year: Premier League Season
    :param min_gw: The minimum number of game weeks a player must have played the specified minutes
    :param min_minutes: The minimum number of minutes a player must have played in a game week
    :return: Filtered DataFrame
    """
    # Determine the correct file path
    project_root = os.path.dirname(os.path.dirname(__file__))  # Navigate to the project root
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(project_root, "fpl-data", current_date, "data", year, "gws", "merged_gw.csv")

    # Check if the file exists, if not, download the repository
    if not os.path.exists(file_path):
        print(f"{file_path} does not exist. Cloning the repository...")
        clone_fpl_repo()  # Call the clone function from the get_repo file

    # Load the CSV file
    df = pd.read_csv(file_path)

    # Calculate the number of game weeks each player played at least the specified minutes
    player_gw_count = df[df["minutes"] >= min_minutes].groupby("element")["GW"].count()
    eligible_players = player_gw_count[player_gw_count >= min_gw].index

    # Print the number of eligible players
    print(f"Number of eligible players (played at least {min_minutes} minutes in at least {min_gw} game weeks): {len(eligible_players)}")

    # Filter and return the DataFrame with only eligible players
    return df[df["element"].isin(eligible_players)]


def load_and_filter_all_seasons_data(min_gw=10, min_minutes=60):
    """
    Loads the CSV file containing data from multiple seasons, filters out players who played fewer than the specified minutes
    in the specified number of game weeks, and updates the element_id to be unique per season.

    :param min_gw: The minimum number of game weeks a player must have played the specified minutes
    :param min_minutes: The minimum number of minutes a player must have played in a game week
    :return: Filtered DataFrame with unique element_id per season
    """
    project_root = os.path.dirname(os.path.dirname(__file__))  # Navigate to the project root
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(project_root, "fpl-data", current_date, "data", "cleaned_merged_seasons.csv")

    # Check if the file exists, if not, download the repository
    if not os.path.exists(file_path):
        print(f"{file_path} does not exist. Cloning the repository...")
        clone_fpl_repo()  # Call the clone function from the get_repo file

    # Load the CSV file with dtype specified and low_memory=False to avoid DtypeWarning
    dtype_dict = {"column_name": str}  # Replace "column_name" with the name of the column(s) causing issues
    df = pd.read_csv(file_path, dtype=dtype_dict, low_memory=False)

    # Update element_id to be unique per season by appending the season
    df["element"] = df["element"].astype(str) + "-" + df["season_x"]

    # Calculate the number of game weeks each player played at least the specified minutes
    player_gw_count = df[df["minutes"] >= min_minutes].groupby("element")["GW"].count()
    eligible_players = player_gw_count[player_gw_count >= min_gw].index

    # Print the number of eligible players
    print(f"Number of eligible players (played at least {min_minutes} minutes in at least {min_gw} game weeks): {len(eligible_players)}")

    # Filter and return the DataFrame with only eligible players
    return df[df["element"].isin(eligible_players)]


def calculate_ict_to_next_gw_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between ICT index and next game week's total points
    correlation = df["ict_index"].corr(df["next_gw_points"])

    print(f"Correlation between ICT index and next game week's total points: {correlation}")

    return correlation

def calculate_avg_ict_to_next_gw_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average of the ICT index for the previous 3 game weeks
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between the average ICT index of the last 3 weeks and the next game week's total points
    correlation = df["avg_ict_last_3_gw"].corr(df["next_gw_points"])

    print(f"Correlation between average ICT index of last 3 game weeks and next game week's total points: {correlation}")

    return correlation

def calculate_expected_goal_involvements_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Filter for only midfielders (position == 'MID') and forwards (position == 'FWD')
    df = df[(df['position'] == 'MID') | (df['position'] == 'FWD')]

    # Calculate the rolling average of expected goal involvements for the last 3 game weeks
    df["avg_expected_goal_involvements_last_3_gw"] = df.groupby("element")["expected_goal_involvements"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between the average expected goal involvements of the last 3 weeks and the next game week's total points
    correlation = df["avg_expected_goal_involvements_last_3_gw"].corr(df["next_gw_points"])

    print(f"Correlation between average expected goal involvements (last 3 weeks) and next game week's total points for MID/FWD: {correlation}")

    return correlation

def find_best_correlation():
    df = load_and_filter_all_seasons_data()

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing
    df = df.dropna(subset=["next_gw_points"])

    correlations = {}

    # Iterate over each numeric column (excluding 'element', 'GW', and 'next_gw_points')
    for column in df.select_dtypes(include=['float64', 'int64']).columns:
        if column not in ["element", "GW", "next_gw_points"]:
            # Calculate the rolling average of the column for the last 3 game weeks
            df[f"avg_{column}_last_3_gw"] = df.groupby("element")[column].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

            # Calculate the correlation with next game week's total points
            correlation = df[f"avg_{column}_last_3_gw"].corr(df["next_gw_points"])
            correlations[column] = correlation

            print(f"Correlation between average of last 3 weeks of {column} and next week's total points: {correlation}")

    # Find the column with the highest correlation
    best_column = max(correlations, key=correlations.get)
    best_correlation = correlations[best_column]

    print(f"\nBest correlated column: {best_column} with correlation of {best_correlation}")

    return correlations, best_column, best_correlation


# Example usage
if __name__ == "__main__":
    calculate_ict_to_next_gw_correlation()
    calculate_avg_ict_to_next_gw_correlation()
    calculate_expected_goal_involvements_correlation()
    find_best_correlation()

import requests
import pandas as pd
import os
from datetime import datetime
from get_repo import clone_fpl_repo


def fetch_api_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data['elements']
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def get_fpl_data(source='github'):
    if source == 'api':
        return fetch_api_data()
    elif source == 'github':
        return clone_fpl_repo()
    else:
        print("Invalid source specified. Use 'api' or 'github'.")
        return None


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
    print(f"Number of filtered players (played at least {min_minutes} minutes in at least {min_gw} game weeks): {len(eligible_players)}")

    # Filter and return the DataFrame with only eligible players
    return df[df["element"].isin(eligible_players)]

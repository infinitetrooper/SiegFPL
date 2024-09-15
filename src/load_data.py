import json
import pandas as pd
import os
from datetime import datetime
from get_data import clone_fpl_repo, fetch_team_gw_data

def load_and_filter_data(year="2023-24", min_gw=10, min_minutes=60):
    """
    Loads the CSV file, filters out players who played fewer than the specified minutes in the specified number of game weeks,
    and returns the filtered DataFrame with "GKP" converted to "GK".

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

    # Convert "GKP" to "GK" in the position column
    df["position"] = df["position"].replace("GKP", "GK")

    # Calculate the number of game weeks each player played at least the specified minutes
    player_gw_count = df[df["minutes"] >= min_minutes].groupby("element")["GW"].count()
    eligible_players = player_gw_count[player_gw_count >= min_gw].index

    # Print the number of eligible players
    print(f"Number of filtered players for {year} who (played at least {min_minutes} minutes in at least {min_gw} game weeks): {len(eligible_players)}")

    # Filter and return the DataFrame with only eligible players
    return df[df["element"].isin(eligible_players)]

def load_and_filter_all_seasons_data(min_gw=10, min_minutes=60):
    """
    Loads the CSV file containing data from multiple seasons, filters out players who played fewer than the specified minutes
    in the specified number of game weeks, converts "GKP" to "GK", and updates the element_id to be unique per season.

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

    # Convert "GKP" to "GK" in the position column
    df["position"] = df["position"].replace("GKP", "GK")

    # Update element_id to be unique per season by appending the season
    df["element"] = df["element"].astype(str) + "-" + df["season_x"]

    # Calculate the number of game weeks each player played at least the specified minutes
    player_gw_count = df[df["minutes"] >= min_minutes].groupby("element")["GW"].count()
    eligible_players = player_gw_count[player_gw_count >= min_gw].index

    # Filter and return the DataFrame with only eligible players
    return df[df["element"].isin(eligible_players)]

def load_latest_data():
    """
    Loads the latest player data from the JSON file in the fpl-data directory.

    :return: List of player data from the JSON file
    """
    # Determine the project root and build the path to the fpl-data folder
    project_root = os.path.dirname(os.path.dirname(__file__))
    fpl_data_dir = os.path.join(project_root, "fpl-data")

    # Determine the file name based on the current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(fpl_data_dir, f"{current_date}.json")

    # Load the JSON data from the file
    if os.path.exists(file_path):
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
            print(f"Loaded data from {file_path}")
            return data['elements']
    else:
        raise FileNotFoundError(f"Data file not found: {file_path}")

def load_team_data(gw, team_id=1365773):
    """
    Loads the saved FPL data from {project root}/fpl-data into a Pandas DataFrame using today's date.
    If the file does not exist, it fetches the data first and then loads it.
    Merges additional player data from the latest available data.

    Args:
        team_id (int): The team ID.
        gw (int): The game week.

    Returns:
        pd.DataFrame: A DataFrame containing the FPL data, including the latest player information.
    """
    # Get today's date in the format YYYY-MM-DD
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Determine the project root and the file path
    project_root = os.path.dirname(os.path.dirname(__file__))
    fpl_data_dir = os.path.join(project_root, "fpl-data")
    file_path = os.path.join(fpl_data_dir, f"{team_id}_gw_{gw}_{current_date}.json")

    # Check if the file exists, if not fetch the data
    if not os.path.exists(file_path):
        print(f"Data file not found for team {team_id} in GW {gw}. Fetching data...")
        fetch_team_gw_data(gw, team_id)  # Fetch the data if it doesn't exist

        # Double-check if the file was saved correctly
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Failed to fetch data for team {team_id} in GW {gw}. File not found after fetch attempt.")

    # Load the JSON data
    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
    except Exception as e:
        raise FileNotFoundError(f"Failed to load data from {file_path}: {str(e)}")

    # Convert the JSON data to a Pandas DataFrame
    picks = data.get("picks", [])

    if not picks:
        raise ValueError(f"No picks data found in the loaded file for team {team_id} in GW {gw}.")

    df = pd.DataFrame(picks)

    # Load the latest data
    latest_data = load_latest_data()

    # Merge the latest data into the picks DataFrame
    if latest_data is not None:
        # Create a DataFrame from the latest_data
        latest_df = pd.DataFrame(latest_data)

        # Rename specific columns
        latest_df.rename(columns={"id": "element", "web_name": "name"}, inplace=True)

        # Map to convert element_type to position
        position_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}

        # Merge with the picks DataFrame, prioritizing element_type from latest_df
        df = pd.merge(df, latest_df, on="element", how="left", suffixes=('', '_drop'))

        # Use the element_type from latest_df to set the position in the final df
        df['position'] = df['element_type'].map(position_map)

        # Drop any unnecessary columns from the original df that were replaced by latest_df
        df = df.drop([col for col in df.columns if '_drop' in col], axis=1)

    name_column = "web_name" if "web_name" in df.columns else "name"
    return df

def create_current_team_df(picks_df, player_data):
    """
    Merges additional columns from player_data into picks_df using the 'element' field without adding suffixes,
    ensuring that overlapping columns retain values from picks_df.

    Args:
        picks_df (pd.DataFrame): A DataFrame representing the picks data.
        player_data (pd.DataFrame): The player data containing details for all available players.

    Returns:
        pd.DataFrame: The updated picks_df with merged data from player_data, retaining picks_df values on overlap.
    """
    # Ensure picks_df is a DataFrame
    if not isinstance(picks_df, pd.DataFrame):
        raise TypeError("Expected picks_df to be a DataFrame.")

    # Ensure there are no duplicate entries based on the 'element' column in both DataFrames
    picks_df = picks_df.drop_duplicates(subset=['element'])
    player_data = player_data.drop_duplicates(subset=['element'])

    # Perform the merge
    updated_picks_df = pd.merge(picks_df, player_data, on="element", how="left", suffixes=('', '_y'))

    # Iterate over the columns in picks_df
    for col in picks_df.columns:
        if col in updated_picks_df.columns:
            # Overwrite the merged columns with picks_df values if there's an overlap
            updated_picks_df[col] = updated_picks_df[f"{col}"]

    # Drop any extra columns created from the merge that have the "_y" suffix
    updated_picks_df = updated_picks_df.drop([col for col in updated_picks_df.columns if col.endswith('_y')], axis=1)

    return updated_picks_df

if __name__ == "__main__":
    load_team_data(gw=3)
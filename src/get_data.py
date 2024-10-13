import json
import os
import shutil
import requests
from git import Repo
from datetime import datetime
import time

def download_file_from_github(file_path, local_path):
    """
    Downloads a file from a GitHub repository and saves it locally.
    
    Args:
    repo_url (str): The base URL of the GitHub repository.
    file_path (str): The path to the file within the repository.
    local_path (str): The local path where the file should be saved.
    """
    repo_url="https://github.com/vaastav/Fantasy-Premier-League"
    
    # Construct the raw content URL
    raw_url = f"{repo_url}/raw/master/{file_path}"

    print(f"Downloading file from {raw_url}...")
    
    # Send a GET request to the URL
    response = requests.get(raw_url)
    
    if response.status_code == 200:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Write the content to the local file
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"File successfully downloaded to {local_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

def fetch_api_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Determine the project root and create the fpl-data directory if it does not exist
        project_root = os.path.dirname(os.path.dirname(__file__))
        fpl_data_dir = os.path.join(project_root, "fpl-data")
        os.makedirs(fpl_data_dir, exist_ok=True)

        # Save the complete JSON response in the fpl-data folder with the current date as the filename
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(fpl_data_dir, f"{current_date}.json")

        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"API data successfully saved to {file_path}")
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

def fetch_team_gw_data(gw, team_id=1365773):
    """
    Fetches FPL data for a specific team ID and game week, and stores it in the {project root}/fpl-data directory.

    Args:
        team_id (int): The team ID.
        gw (int): The game week.

    Returns:
        None
    """
    # Construct the URL with the provided team_id and game week (gw)
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"

    # Send a GET request to fetch the data
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Determine the project root and create the fpl-data directory if it does not exist
        project_root = os.path.dirname(os.path.dirname(__file__))
        fpl_data_dir = os.path.join(project_root, "fpl-data")
        os.makedirs(fpl_data_dir, exist_ok=True)

        # Determine the file path
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(fpl_data_dir, f"{team_id}_gw_{gw}_{current_date}.json")

        # Check if the file already exists, and delete it if it does
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Existing file {file_path} deleted.")

        # Save the new JSON response to the file
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        # Wait for a short duration to ensure the file is fully written
        time.sleep(0.5)  # Adjust the delay as needed

        print(f"Data for team {team_id} in GW {gw} successfully saved to {file_path}")
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        
if __name__ == "__main__":
    fetch_team_gw_data(gw=3)
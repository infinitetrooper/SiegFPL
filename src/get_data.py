import json
import os
import shutil
import requests
from datetime import datetime

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
    Fetches FPL data for a specific team ID and game week.

    Args:
        team_id (int): The team ID.
        gw (int): The game week.

    Returns:
        JSON
    """
    # Construct the URL with the provided team_id and game week (gw)
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gw}/picks/"

    # Perform the GET request to retrieve data
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {str(e)}")

def cleanup_old_files():
    # Define the path to the fpl-data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fpl_data_dir = os.path.join(project_root, "fpl-data")

    # Get today's date in the format used for filenames
    today = datetime.now().strftime("%Y-%m-%d")

    # List all files and folders in the fpl-data directory
    items = os.listdir(fpl_data_dir)

    # Iterate through the items
    for item in items:
        item_path = os.path.join(fpl_data_dir, item)

        # Check if the item is a directory or an outdated .json file
        if (os.path.isdir(item_path) and item != today) or (item.endswith(".json") and item != f"{today}.json"):
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Deleted old folder: {item_path}")
                else:
                    os.remove(item_path)
                    print(f"Deleted old file: {item}")
            except Exception as e:
                print(f"Error deleting file or folder {item}: {str(e)}")
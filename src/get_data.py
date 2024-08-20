import json
import os
import shutil
import requests
from git import Repo
from datetime import datetime


def clone_fpl_repo():
    # Define the repository URL
    repo_url = "https://github.com/vaastav/Fantasy-Premier-League.git"

    # Generate the folder name with the current date inside the project root
    current_date = datetime.now().strftime("%Y-%m-%d")
    project_root = os.path.dirname(os.path.dirname(__file__))  # Navigate to the project root
    base_directory = os.path.join(project_root, "fpl-data")
    folder_name = os.path.join(base_directory, current_date)
    clone_directory = folder_name

    # Check if today's data already exists
    if os.path.exists(clone_directory):
        print(f"Today's data already exists at {clone_directory}. No need to download again.")
        return clone_directory
    else:
        # Delete existing data in `/fpl-data/` if any
        if os.path.exists(base_directory):
            shutil.rmtree(base_directory)
            print(f"Deleted existing data in {base_directory}.")

        # Create the directory structure and clone the repository
        os.makedirs(clone_directory)
        Repo.clone_from(repo_url, clone_directory)
        fetch_api_data()
        print(f"Repository cloned to {clone_directory}")

    return clone_directory


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

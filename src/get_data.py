import requests
import pandas as pd
import json
import os
from datetime import datetime
from get_repo import clone_fpl_repo

def fetch_fpl_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data['elements']
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def fetch_csv_and_convert_to_json():
    clone_fpl_repo()

    # Determine the directory where the repo was downloaded
    project_root = os.path.dirname(os.path.dirname(__file__))  # Navigate to the project root
    current_date = datetime.now().strftime("%Y-%m-%d")
    csv_file_path = os.path.join(project_root, "fpl-data", current_date, "data", "2024-25", "players_raw.csv")

    # Check if the file exists
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found at {csv_file_path}. Make sure the data has been downloaded.")
        return None

    # Load the CSV data into a pandas DataFrame
    df = pd.read_csv(csv_file_path)

    # Convert the DataFrame to JSON format
    json_data = df.to_json(orient='records', indent=4)

    print("CSV data successfully converted to JSON.")
    return json.loads(json_data)

def get_fpl_data(source='github'):
    if source == 'api':
        return fetch_fpl_data()
    elif source == 'github':
        return fetch_csv_and_convert_to_json()
    else:
        print("Invalid source specified. Use 'api' or 'github'.")
        return None

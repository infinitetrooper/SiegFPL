import requests
import pandas as pd
import json
import io

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
    # URL to the raw CSV file on GitHub
    url = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/players_raw.csv"

    # Fetch the CSV data from the URL
    response = requests.get(url)
    if response.status_code == 200:
        # Load the CSV data into a pandas DataFrame
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))

        # Convert the DataFrame to JSON format
        json_data = df.to_json(orient='records', indent=4)

        print("CSV data successfully converted to JSON.")
        return json.loads(json_data)  # Returning as Python dictionary (list of dicts)
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def get_fpl_data(source='api'):
    if source == 'api':
        return fetch_fpl_data()
    elif source == 'github':
        return fetch_csv_and_convert_to_json()
    else:
        print("Invalid source specified. Use 'api' or 'github'.")
        return None

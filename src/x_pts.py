from sklearn.linear_model import LinearRegression
from src.load_data import load_and_filter_data, load_and_filter_all_seasons_data
import pandas as pd

def calculate_expected_points(df=load_and_filter_all_seasons_data()):
    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Drop duplicates if they exist, keeping only the first instance
    df = df.drop_duplicates(subset=["element", "GW"])
    print(f"Total rows after removing duplicates: {len(df)}")

    # Filter out players who have not played any minutes in a game week
    df = df[df["minutes"] > 0]
    print(f"After filtering out players with 0 minutes: {len(df)} rows")

    # Calculate the rolling average of ICT index for the last 3 game weeks for each player
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)
    print(f"After calculating rolling averages: {len(df)} rows")

    # Filter out rows where avg_ict_last_3_gw is NaN or 0
    df = df.dropna(subset=["avg_ict_last_3_gw"])
    df = df[df["avg_ict_last_3_gw"] != 0]
    print(f"After filtering out NaN or 0 avg_ict_last_3_gw: {len(df)} rows")

    # Split data by position
    position_groups = df.groupby("position")

    # Store models and coefficients for each position
    models = {}
    position_coefficients = {}

    for position, group in position_groups:
        print(f"\nPosition: {position} | Number of players: {group['element'].nunique()} | Total game weeks: {group['GW'].count()}")
        print(f"Number of data points for {position}: {len(group)}")

        # For each position, correlate the last 3 weeks' ICT index average with the current game week's points
        X = group["avg_ict_last_3_gw"].values.reshape(-1, 1)
        y = group["total_points"].values  # Use current game week's points directly

        model = LinearRegression()
        model.fit(X, y)

        # Store the model and coefficients for this position
        models[position] = model
        position_coefficients[position] = {"coef": model.coef_[0], "intercept": model.intercept_}

        # Calculate expected points (xPts) for players in this position
        df.loc[df["position"] == position, "xPts"] = model.predict(X)

        # Print the model coefficients and final points used
        print(f"Model Coefficient (ICT Index Impact): {model.coef_[0]}")
        print(f"Model Intercept: {model.intercept_}")
        print(f"Total points used to train the model for {position}: {y.size}")

    return position_coefficients

def predict_future_xPts(average_ict, position, position_coefficients):
    """
    Predicts the expected points (xPts) based on the 3-week average ICT index for a specific position.

    :param average_ict: The 3-week average ICT index for a player
    :param position: The position of the player (GK, DEF, MID, FWD)
    :param position_coefficients: A dictionary containing the coefficients and intercepts for each position
    :return: Predicted expected points (xPts)
    """
    coef = position_coefficients[position]["coef"]
    intercept = position_coefficients[position]["intercept"]
    return (coef * average_ict) + intercept

if __name__ == "__main__":
    calculate_expected_points()
from statistics import correlation

from sklearn.linear_model import LinearRegression
from src.load_data import load_and_filter_data, load_and_filter_all_seasons_data
import pandas as pd

def calculate_expected_points(df=load_and_filter_data(), criteria="ict_index"):
    """
    Calculates the expected points based on the selected criteria for each position.

    :param df: The input DataFrame containing the filtered game week data.
    :param criteria: The criteria (column) for which to calculate rolling averages and fit models.
    :return: A dictionary with position-based models and coefficients.
    """
    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average for the criteria for the last 3 game weeks
    rolling_avg_column = f"avg_3w_{criteria}"
    df[rolling_avg_column] = df.groupby("element")[criteria].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Filter out rows where the rolling average is NaN or 0
    df = df.dropna(subset=[rolling_avg_column])
    df = df[df[rolling_avg_column] != 0]

    # Split data by position
    position_groups = df.groupby("position")

    # Store models and coefficients for each position
    position_coefficients = {}

    for position, group in position_groups:
        # For each position, correlate the last 3 weeks' average criteria with the current game week's points
        X = group[rolling_avg_column].values.reshape(-1, 1)
        y = group["total_points"].values

        model = LinearRegression()
        model.fit(X, y)

        # Store the model and coefficients for this position
        position_coefficients[position] = {
            "coef": model.coef_[0],
            "intercept": model.intercept_,
            "correlation": model.score(X, y)
        }

        # print(f"Position: {position} | Criteria: {criteria} | Coefficient: {model.coef_[0]} | Intercept: {model.intercept_} | Points Trained: {y.size}")

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
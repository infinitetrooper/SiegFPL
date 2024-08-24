from sklearn.linear_model import LinearRegression
from src.load_data import load_and_filter_data

def calculate_expected_points(df=load_and_filter_data(year="2023-24")):
    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average of ICT index for the last 3 game weeks for all players
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(
        1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing or where avg_ict_last_3_gw is NaN
    df = df.dropna(subset=["next_gw_points", "avg_ict_last_3_gw"])

    # Split data by position
    position_groups = df.groupby("position")

    # Store models and coefficients for each position
    models = {}
    position_coefficients = {}

    for position, group in position_groups:
        X = group["avg_ict_last_3_gw"].values.reshape(-1, 1)
        y = group["next_gw_points"].values

        model = LinearRegression()
        model.fit(X, y)

        # Store the model and coefficients for this position
        models[position] = model
        position_coefficients[position] = {"coef": model.coef_[0], "intercept": model.intercept_}

        # Calculate expected points (xPts) for players in this position
        df.loc[df["position"] == position, "xPts"] = model.predict(X)

        # Print the model coefficients for each position
        print(f"Position: {position}")
        print(f"Model Coefficient (ICT Index Impact): {model.coef_[0]}")
        print(f"Model Intercept: {model.intercept_}")
        print(f"Total points used to train the model for {position}: {y.sum()}\n")

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
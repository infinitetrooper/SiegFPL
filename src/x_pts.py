from sklearn.linear_model import LinearRegression
from correlation import load_and_filter_all_seasons_data

def calculate_expected_points(df):
    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average of ICT index for the last 3 game weeks for all players
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(
        1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing or where avg_ict_last_3_gw is NaN
    df = df.dropna(subset=["next_gw_points", "avg_ict_last_3_gw"])

    # Train a linear regression model to predict points based on the average ICT index for all players combined
    X = df["avg_ict_last_3_gw"].values.reshape(-1, 1)
    y = df["next_gw_points"].values

    model = LinearRegression()
    model.fit(X, y)

    # Calculate expected points (xPts) using the model
    df["xPts"] = model.predict(X)

    # Print the model coefficients
    print(f"Model Coefficient (ICT Index Impact): {model.coef_[0]}")
    print(f"Model Intercept: {model.intercept_}")

    # Calculate and print the total points used to train the model
    total_points = y.sum()
    print(f"Total points used to train the model: {total_points}")

    # Calculate the average xPts across all players
    avg_xPts = df["xPts"].mean()
    print(f"\nAverage Expected Points (xPts) across all players: {avg_xPts}")

    return model.coef_[0], model.intercept_


def predict_future_xPts(average_ict, coef, intercept):
    """
    Predicts the expected points (xPts) based on the 3-week average ICT index.

    :param average_ict: The 3-week average ICT index for a player
    :param coef: The coefficient from the trained linear regression model
    :param intercept: The intercept from the trained linear regression model
    :return: Predicted expected points (xPts)
    """
    return (coef * average_ict) + intercept


# Example usage
if __name__ == "__main__":
    df = load_and_filter_all_seasons_data()
    coef, intercept = calculate_expected_points(df)

    # Example: Predict xPts for a player with a 3-week average ICT index.
    average_ict = 15.2
    predicted_xPts = predict_future_xPts(average_ict, coef, intercept)
    print(f"\nPredicted xPts for a player with 3-week average ICT of {average_ict}: {predicted_xPts}")

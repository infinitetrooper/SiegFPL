from load_data import load_and_filter_data, load_and_filter_all_seasons_data
from src.x_pts import calculate_expected_points


def find_top_coefficients_by_position(min_gw=10, min_minutes=60):
    df = load_and_filter_all_seasons_data(min_gw=min_gw, min_minutes=min_minutes)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Filter out players who have not played any minutes in a game week
    df = df[df["minutes"] > 0]

    # Dictionary to store top coefficients by position
    coefficients_by_position = {}

    # Define the positions to iterate over
    positions = {
        'GK': 'Goalkeepers',
        'DEF': 'Defenders',
        'MID': 'Midfielders',
        'FWD': 'Forwards'
    }

    # Iterate over each position
    for position_code, position_name in positions.items():
        # Create a copy of the filtered position data
        position_df = df[df['position'] == position_code].copy()

        # Check if there's enough data for the position
        if position_df.empty:
            print(f"\nSkipping {position_name} due to insufficient data.")
            continue

        # Dictionary to store coefficients for this position
        coefficients = {}

        # Iterate over each numeric column (excluding 'element', 'GW', and 'total_points')
        for column in position_df.select_dtypes(include=['float64', 'int64']).columns:
            if column not in ["element", "GW", "total_points"]:
                # Skip columns with fewer than 500 rows of data
                if position_df[column].count() < 500:
                    print(f"Skipping column '{column}' for {position_name} due to insufficient data (< 500 rows).")
                    continue

                # Use calculate_expected_points for each column as criteria
                coefficients_data = calculate_expected_points(position_df, criteria=column)

                # Ensure the coefficients data contains the required position
                if position_code in coefficients_data:
                    coef = coefficients_data[position_code]["coef"]
                    intercept = coefficients_data[position_code]["intercept"]
                    points_trained = position_df[column].count()

                    # Store the coefficients and points trained for this column
                    coefficients[column] = (abs(coef), coef, intercept, points_trained)
                else:
                    print(
                        f"Skipping column '{column}' for {position_name} due to insufficient data or model training issues.")

            # Store all coefficients for this position
            coefficients_by_position[position_code] = coefficients

    # Return the results after processing all positions
    return coefficients_by_position

# Example usage
if __name__ == "__main__":
    find_top_coefficients_by_position()

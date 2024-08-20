from get_data import load_and_filter_data, load_and_filter_all_seasons_data

def calculate_ict_to_next_gw_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between ICT index and next game week's total points
    correlation = df["ict_index"].corr(df["next_gw_points"])

    print(f"Correlation between ICT index and next game week's total points: {correlation}")

    return correlation

def calculate_avg_ict_to_next_gw_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average of the ICT index for the previous 3 game weeks
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between the average ICT index of the last 3 weeks and the next game week's total points
    correlation = df["avg_ict_last_3_gw"].corr(df["next_gw_points"])

    print(f"Correlation between average ICT index of last 3 game weeks and next game week's total points: {correlation}")

    return correlation

def calculate_avg_ict_correlation_by_position():
    df = load_and_filter_all_seasons_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Calculate the rolling average of the ICT index for the previous 3 game weeks
    df["avg_ict_last_3_gw"] = df.groupby("element")["ict_index"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing
    df = df.dropna(subset=["next_gw_points"])

    # Define a dictionary to store correlations for each position
    correlations = {}

    # Calculate correlations for each position (GK, DEF, MID, FWD)
    positions = {
        'GK': 'Goalkeepers',
        'DEF': 'Defenders',
        'MID': 'Midfielders',
        'FWD': 'Forwards'
    }

    for position_code, position_name in positions.items():
        position_df = df[df['position'] == position_code]

        # Calculate the correlation between the average ICT index of the last 3 weeks and the next game week's total points
        correlation = position_df["avg_ict_last_3_gw"].corr(position_df["next_gw_points"])

        correlations[position_code] = correlation
        print(f"Correlation between average ICT index of last 3 game weeks and next game week's total points for {position_name}: {correlation}")

    return correlations

def calculate_expected_goal_involvements_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Filter for only midfielders (position == 'MID') and forwards (position == 'FWD')
    df = df[(df['position'] == 'MID') | (df['position'] == 'FWD')]

    # Calculate the rolling average of expected goal involvements for the last 3 game weeks
    df["avg_expected_goal_involvements_last_3_gw"] = df.groupby("element")["expected_goal_involvements"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points"])

    # Calculate the correlation between the average expected goal involvements of the last 3 weeks and the next game week's total points
    correlation = df["avg_expected_goal_involvements_last_3_gw"].corr(df["next_gw_points"])

    print(f"Correlation between average expected goal involvements (last 3 weeks) and next game week's total points for MID/FWD: {correlation}")

    return correlation

def calculate_expected_goals_conceded_correlation():
    df = load_and_filter_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Filter for only defenders (position == 'DEF') and goalkeepers (position == 'GK')
    df = df[(df['position'] == 'DEF') | (df['position'] == 'GK')]

    # Calculate the rolling average of expected goals conceded for the last 3 game weeks
    df["avg_expected_goals_conceded_last_3_gw"] = df.groupby("element")["expected_goals_conceded"].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing (i.e., the last game week a player played)
    df = df.dropna(subset=["next_gw_points", "avg_expected_goals_conceded_last_3_gw"])

    # Calculate the correlation between the average expected goals conceded of the last 3 weeks and the next game week's total points
    # Since lower expected goals conceded is better, we multiply the correlation by -1
    correlation = df["avg_expected_goals_conceded_last_3_gw"].corr(df["next_gw_points"]) * -1

    print(f"Correlation between average expected goals conceded (last 3 weeks) and next game week's total points for DEF/GK (adjusted for lower being better): {correlation}")

    return correlation

def find_best_correlation():
    df = load_and_filter_all_seasons_data(min_gw=10, min_minutes=60)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing
    df = df.dropna(subset=["next_gw_points"])

    correlations = {}

    # Iterate over each numeric column (excluding 'element', 'GW', and 'next_gw_points')
    for column in df.select_dtypes(include=['float64', 'int64']).columns:
        if column not in ["element", "GW", "next_gw_points"]:
            # Calculate the rolling average of the column for the last 3 game weeks
            df[f"avg_{column}_last_3_gw"] = df.groupby("element")[column].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

            # Calculate the correlation with next game week's total points
            correlation = df[f"avg_{column}_last_3_gw"].corr(df["next_gw_points"])
            correlations[column] = correlation

            print(f"Correlation between average of last 3 weeks of {column} and next week's total points: {correlation}")

    # Find the column with the highest correlation
    best_column = max(correlations, key=correlations.get)
    best_correlation = correlations[best_column]

    print(f"\nBest correlated column: {best_column} with correlation of {best_correlation}")

    return correlations, best_column, best_correlation

def find_best_correlation_by_position(min_gw=10, min_minutes=60):
    df = load_and_filter_all_seasons_data(min_gw=min_gw, min_minutes=min_minutes)

    # Ensure the data is sorted by player (element) and game week (GW)
    df = df.sort_values(by=["element", "GW"])

    # Shift the total points column by -1 for each player to get next game week's points
    df["next_gw_points"] = df.groupby("element")["total_points"].shift(-1)

    # Filter out rows where the next game week's points are missing
    df = df.dropna(subset=["next_gw_points"])

    # Define a dictionary to store correlations for each position
    correlations_by_position = {}

    # Define the positions to iterate over
    positions = {
        'GK': 'Goalkeepers',
        'DEF': 'Defenders',
        'MID': 'Midfielders',
        'FWD': 'Forwards'
    }

    for position_code, position_name in positions.items():
        # Create a copy of the filtered position data to avoid SettingWithCopyWarning
        position_df = df[df['position'] == position_code].copy()

        correlations = {}

        # Iterate over each numeric column (excluding 'element', 'GW', and 'next_gw_points')
        for column in position_df.select_dtypes(include=['float64', 'int64']).columns:
            if column not in ["element", "GW", "next_gw_points"]:
                # Skip columns with zero variance (standard deviation of 0)
                if position_df[column].std() == 0:
                    continue

                # Calculate the rolling average of the column for the last 3 game weeks
                position_df[f"avg_{column}_last_3_gw"] = position_df.groupby("element")[column].rolling(window=3, min_periods=1).mean().shift(1).reset_index(level=0, drop=True)

                # Drop any remaining NaN values
                position_df = position_df.dropna(subset=[f"avg_{column}_last_3_gw", "next_gw_points"])

                # Calculate the correlation with next game week's total points
                correlation = position_df[f"avg_{column}_last_3_gw"].corr(position_df["next_gw_points"])
                correlations[column] = correlation

                print(f"{position_name}: Correlation between average of last 3 weeks of {column} and next week's total points: {correlation}")

        # Find the column with the highest correlation for this position
        if correlations:
            best_column = max(correlations, key=correlations.get)
            best_correlation = correlations[best_column]

            print(f"\n{position_name}: Best correlated column: {best_column} with correlation of {best_correlation}\n")

            # Store the correlations for this position
            correlations_by_position[position_code] = (correlations, best_column, best_correlation)

    return correlations_by_position

# Example usage
if __name__ == "__main__":
    calculate_avg_ict_correlation_by_position()
    find_best_correlation_by_position()
    """calculate_ict_to_next_gw_correlation()
    calculate_avg_ict_to_next_gw_correlation()
    calculate_expected_goal_involvements_correlation()
    calculate_expected_goals_conceded_correlation()
    find_best_correlation()"""

import pandas as pd

# Current date in yyyy-mm-dd format
current_date = pd.Timestamp.now().strftime("%Y-%m-%d")

# Load merged_gw and fixtures data
merged_gw_path = f'fpl-data/{current_date}/data/2023-24/gws/merged_gw.csv'
fixtures_path = f'fpl-data/{current_date}/data/2023-24/fixtures.csv'

merged_gw = pd.read_csv(merged_gw_path)
fixtures = pd.read_csv(fixtures_path)

merged_gw['GW'] = merged_gw['GW'].astype(int)
fixtures['event'] = fixtures['event'].astype(int)

# Filter out players who have not played any minutes
to_include = merged_gw['minutes'] > 0
merged_gw = merged_gw[to_include]

# Replace 'event' with 'gw' in fixtures DataFrame
fixtures = fixtures.rename(columns={'event': 'GW'})
fixtures = fixtures.rename(columns={'id': 'fixture'})

# Merge fixtures and merged_gw on 'GW' and fixture
# List of columns that are causing a conflict
conflicting_columns = ['kickoff_time', 'minutes', 'team_a_score', 'team_h_score']

# Drop conflicting columns from fixtures
fixtures = fixtures.drop(columns=conflicting_columns)

# Now merge the DataFrames without suffixes
merged_gw = merged_gw.merge(fixtures, on=['GW', 'fixture'], how='left', indicator=False)

# Print the number of rows
print(f'Number of rows: {merged_gw.shape[0]}')


# Calculate effective difficulty based on home/away status
merged_gw['effective_difficulty'] = merged_gw.apply(
		lambda row: row['team_h_difficulty'] if row['was_home'] == 1 else row['team_a_difficulty'], axis=1
)

# Ensure 'total_points' is numeric
merged_gw['total_points'] = pd.to_numeric(merged_gw['total_points'], errors='coerce')

# Drop rows with NaN total_points
merged_gw = merged_gw.dropna(subset=['total_points'])

# Calculate average total points for difficulty
avg_points_by_difficulty = merged_gw.groupby(['position', 'effective_difficulty'])['total_points'].mean().reset_index()

# Calculate average total points for position
avg_points_by_position = merged_gw.groupby(['position'])['total_points'].mean().reset_index()

# Calculate average difficulty for position
avg_difficulty_by_position = merged_gw.groupby(['position'])['effective_difficulty'].mean().reset_index()

# Write the merged_gw DataFrame to a CSV file
output_path = f'fpl-data/{current_date}/data/2023-24/merged_fixture_difficulty.csv'
merged_gw.to_csv(output_path, index=False)

print(avg_points_by_difficulty)
print(avg_points_by_position)
print(avg_difficulty_by_position)

# import matplotlib.pyplot as plt

# # Plot avg_points_by_difficulty on a graph
# plt.figure(figsize=(10, 6))
# for position in avg_points_by_difficulty['position'].unique():
#     subset = avg_points_by_difficulty[avg_points_by_difficulty['position'] == position]
#     plt.plot(subset['effective_difficulty'], subset['total_points'], marker='o', label=position)

# plt.title('Average Points by Effective Difficulty')
# plt.xlabel('Effective Difficulty')
# plt.ylabel('Average Total Points')
# plt.legend(title='Position')
# plt.grid(True)
# plt.show()

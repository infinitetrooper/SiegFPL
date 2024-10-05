import pandas as pd
import load_data

def scale_pts_by_difficulty():
	merged_gw = load_data.load_and_filter_data(year="2023-24")
	fixtures = load_data.load_fixture_data(year="2023-24")
	
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
	merged_gw['difficulty'] = merged_gw.apply(
			lambda row: row['team_h_difficulty'] if row['was_home'] == 1 else row['team_a_difficulty'], axis=1
	)
	
	# Ensure 'total_points' is numeric
	merged_gw['total_points'] = pd.to_numeric(merged_gw['total_points'], errors='coerce')
	
	# Drop rows with NaN total_points
	merged_gw = merged_gw.dropna(subset=['total_points'])
	
	# Calculate average total points for difficulty
	avg_points_by_difficulty = merged_gw.groupby(['position', 'difficulty'])['total_points'].mean().reset_index()
	
	# Calculate average total points for position
	avg_points_by_position = merged_gw.groupby(['position'])['total_points'].mean().reset_index()
	
	# Calculate average difficulty for position
	avg_difficulty_by_position = merged_gw.groupby(['position'])['difficulty'].mean().reset_index()
	
	# Add 'scale_factor' column to avg_points_by_difficulty dataframe
	avg_points_by_difficulty = avg_points_by_difficulty.merge(
	    avg_points_by_position[['position', 'total_points']],
	    on='position',
	    suffixes=('', '_avg')
	)
	avg_points_by_difficulty['scale_factor'] = avg_points_by_difficulty['total_points'] / avg_points_by_difficulty['total_points_avg']
	
	del avg_points_by_difficulty['total_points_avg']
	del avg_points_by_difficulty['total_points']

	return avg_points_by_difficulty
	
if __name__ == "__main__":
	print(scale_pts_by_difficulty())
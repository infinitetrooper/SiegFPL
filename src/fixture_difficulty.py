import pandas as pd
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm  # For detailed statistical analysis
import matplotlib.pyplot as plt

# Load merged_gw and fixtures data
merged_gw_path = 'fpl-data/2024-09-21/data/2023-24/gws/merged_gw.csv'
fixtures_path = 'fpl-data/2024-09-21/data/2023-24/fixtures.csv'

merged_gw = pd.read_csv(merged_gw_path)
fixtures = pd.read_csv(fixtures_path)

# Merge merged_gw with fixtures on 'GW' and 'team_h'/'team_a' depending on home/away fixtures
merged_gw['GW'] = merged_gw['GW'].astype(int)
fixtures['event'] = fixtures['event'].astype(int)

# Create columns to join on
fixtures_home = fixtures[['event', 'team_h', 'team_h_difficulty']]
fixtures_home = fixtures_home.rename(columns={'team_h': 'team', 'team_h_difficulty': 'fixture_difficulty'})
fixtures_away = fixtures[['event', 'team_a', 'team_a_difficulty']]
fixtures_away = fixtures_away.rename(columns={'team_a': 'team', 'team_a_difficulty': 'fixture_difficulty'})

# Concatenate home and away fixtures
all_fixtures = pd.concat([fixtures_home, fixtures_away])

# Ensure 'team' columns in both DataFrames are of type `object` (string)

# Convert 'team' column in merged_gw DataFrame to string
merged_gw['team'] = merged_gw['team'].astype(str)

# Convert 'team' column in all_fixtures DataFrame to string
all_fixtures['team'] = all_fixtures['team'].astype(str)

# Then, merge the DataFrames
merged_data = merged_gw.merge(all_fixtures, left_on=['GW', 'team'], right_on=['event', 'team'], how='left')

# Check for missing values in fixture_difficulty column and fill them
merged_data['fixture_difficulty'].fillna(0, inplace=True)  # Fill with 0 if there are missing values

# Prepare the data for regression
X = merged_data[['fixture_difficulty']]
y = merged_data['total_points']

# Add a constant to the model (required for statsmodels)
X = sm.add_constant(X)

# Fit the regression model using statsmodels
model = sm.OLS(y, X).fit()

# Print the summary of the regression
print(model.summary())

# Alternatively, use sklearn LinearRegression
# model = LinearRegression()
# model.fit(X, y)
# print(f"Coefficient: {model.coef_}")
# print(f"Intercept: {model.intercept_}")
# print(f"R^2 Score: {model.score(X, y)}")

# Plotting the relationship (optional)
plt.scatter(X['fixture_difficulty'], y, color='blue')
plt.plot(X['fixture_difficulty'], model.predict(X), color='red')
plt.xlabel('Fixture Difficulty')
plt.ylabel('Total Points')
plt.title('Fixture Difficulty vs Player Points')
plt.show()
import pandas as pd
import statsmodels.api as sm  # For detailed statistical analysis
import matplotlib.pyplot as plt

# Current date in yyyy-mm-dd format
current_date = pd.Timestamp.now().strftime("%Y-%m-%d")

# Load merged_gw and fixtures data
merged_gw_path = f'fpl-data/{current_date}/data/2023-24/gws/merged_gw.csv'
fixtures_path = f'fpl-data/{current_date}/data/2023-24/fixtures.csv'

merged_gw = pd.read_csv(merged_gw_path)
fixtures = pd.read_csv(fixtures_path)

# Merge merged_gw with fixtures on 'GW' and 'team_h'/'team_a' depending on home/away fixtures
merged_gw['GW'] = merged_gw['GW'].astype(int)
fixtures['event'] = fixtures['event'].astype(int)

# Replace 'event' with 'gw' in fixtures DataFrame
fixtures = fixtures.rename(columns={'event': 'GW'})
fixtures = fixtures.rename(columns={'id': 'fixture'})

# Merge fixtures and merged_gw on 'GW' and fixture
merged_gw = merged_gw.merge(fixtures, on=['GW', 'fixture'], how='left')


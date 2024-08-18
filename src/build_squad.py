import json


def pick_best_squad(data, budget=1000):
    # Limit the player pool based on the number of players per position sorted by ict_index
    goalkeepers = sorted([p for p in data if p['element_type'] == 1], key=lambda x: float(x['ict_index']),
                         reverse=True)[:10]
    defenders = sorted([p for p in data if p['element_type'] == 2], key=lambda x: float(x['ict_index']), reverse=True)[
                :25]
    midfielders = sorted([p for p in data if p['element_type'] == 3], key=lambda x: float(x['ict_index']),
                         reverse=True)[:25]
    forwards = sorted([p for p in data if p['element_type'] == 4], key=lambda x: float(x['ict_index']), reverse=True)[
               :15]

    # Pick the best 2 goalkeepers, 5 defenders, 5 midfielders, and 3 forwards within the budget
    selected_goalkeepers = goalkeepers[:2]
    selected_defenders = defenders[:5]
    selected_midfielders = midfielders[:5]
    selected_forwards = forwards[:3]

    squad = selected_goalkeepers + selected_defenders + selected_midfielders + selected_forwards

    iteration = 0  # To track the number of iterations

    # Run simulations until a squad within the budget is found
    while True:
        iteration += 1

        squad_cost = sum(player['now_cost'] for player in squad)
        print(f"Iteration {iteration}: Squad cost = {squad_cost}")

        if squad_cost <= budget:
            break  # Exit loop if budget is satisfied

        # If the budget is exceeded, attempt to replace the least expensive player first
        for player in sorted(squad, key=lambda x: x['now_cost']):
            available_replacements = [p for p in (goalkeepers + defenders + midfielders + forwards)
                                      if p['element_type'] == player['element_type'] and
                                      p not in squad and p['now_cost'] < player['now_cost']]

            if available_replacements:
                # Replace the player with the best available cheaper replacement
                replacement = sorted(available_replacements, key=lambda x: float(x['ict_index']), reverse=True)[0]
                squad[squad.index(player)] = replacement
                print(player['web_name'], replacement['web_name'])
                break
        else:
            # If no valid replacements are found for this player, try replacing the next player on the list
            continue

    # From this squad, pick the best 11 with at least 1 GK, 3 DEF, 3 MID, and 1 FWD
    selected_goalkeepers = [p for p in squad if p['element_type'] == 1]
    selected_defenders = [p for p in squad if p['element_type'] == 2]
    selected_midfielders = [p for p in squad if p['element_type'] == 3]
    selected_forwards = [p for p in squad if p['element_type'] == 4]

    best_11 = (
            sorted(selected_goalkeepers, key=lambda x: float(x['ict_index']), reverse=True)[:1] +
            sorted(selected_defenders, key=lambda x: float(x['ict_index']), reverse=True)[:3] +
            sorted(selected_midfielders, key=lambda x: float(x['ict_index']), reverse=True)[:3] +
            sorted(selected_forwards, key=lambda x: float(x['ict_index']), reverse=True)[:1]
    )

    # Ensure no duplicate players in the starting 11
    remaining_spots = 11 - len(best_11)
    remaining_players = sorted(selected_goalkeepers + selected_defenders + selected_midfielders + selected_forwards,
                               key=lambda x: float(x['ict_index']), reverse=True)

    # Filter out already selected players from remaining players
    remaining_players = [player for player in remaining_players if player not in best_11]

    for player in remaining_players:
        if remaining_spots > 0:
            best_11.append(player)
            remaining_spots -= 1

    # Pick a captain from the best 11 based on the highest ict_index
    captain = max(best_11, key=lambda x: float(x['ict_index']))

    return squad, best_11, captain

# Example usage:
# Assuming you have loaded your data as `fpl_data` from the JSON
# squad, best_11, captain = pick_best_squad(fpl_data)

# Print out the selected squad, best 11, and captain

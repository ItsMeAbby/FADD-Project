import os
import pandas as pd
from pandas import DataFrame
import numpy as np
from collections import defaultdict
from datetime import datetime
import logging
import json
from dotenv import load_dotenv

load_dotenv(override=True)

# Assuming fetch_data.py and models.py exist and contain necessary definitions
from utils.db import cal_time_passed, save_last_updated_time, save_to_duckdb
from utils.fetch_data import DataFetcher

def fetch_all_data(league: str, current_season: int, fetch_again: bool = False) -> dict:
    """
    Fetch or load all required data for current and previous season.
    
    Args:
        league (str): League identifier
        current_season (int): Current season year
        fetch_again (bool): Whether to fetch fresh data from API
        
    Returns:
        Dict: Dictionary containing all fetched/loaded data
    """
    data = {
        "standings": {},
        "matches": {}
    }
    
    # Handle current season
    current_fetcher = DataFetcher(current_season=current_season, league=league)
    
    if fetch_again:
        for endpoint in ["standings", "matches"]:
            json_data = current_fetcher.get_data(endpoint)
            if json_data:
                if endpoint == "standings":
                    data[endpoint][current_season] = json_data["standings"][0]["table"]
                elif endpoint == "matches":
                    data[endpoint][current_season] = json_data["matches"]
                current_fetcher.save_data(endpoint, data[endpoint][current_season])
    else:
        for endpoint in ["standings", "matches"]:
            data[endpoint][current_season] = current_fetcher.load_data(endpoint)
    
    # Handle previous season
    previous_season = current_season - 1
    previous_fetcher = DataFetcher(current_season=previous_season, league=league)
    if fetch_again:
        for endpoint in ["standings", "matches"]:
            json_data = previous_fetcher.get_data(endpoint)
            if json_data:
                if endpoint == "standings":
                    data[endpoint][previous_season] = json_data["standings"][0]["table"]
                elif endpoint == "matches":
                    data[endpoint][previous_season] = json_data["matches"]
                previous_fetcher.save_data(endpoint, data[endpoint][previous_season])
    else:
        for endpoint in ["standings", "matches"]:
            data[endpoint][previous_season] = previous_fetcher.load_data(endpoint)
    
    return data

def adjust_team_name(team_name: str):
    """Simplifies team names by removing 'FC', 'AFC', and replacing '&' with 'and'."""
    return team_name.replace(" FC", "").replace("AFC ", "").replace("&", "and").strip()

def extract_team_names(data: dict, season: int):
    """Extracts and cleans team names from standings data for a specific season."""
    standings = data["standings"][season]
    teams = [adjust_team_name(entry["team"]["name"]) for entry in standings]
    return teams

def get_standings(data: dict, curr_season: int, num_past_seasons: int = 2, show: bool = False):
    """
    Constructs a DataFrame containing league standings for each season, in long format.
    """
    standings_list = []

    # Extract list of teams for the current season
    team_list = extract_team_names(data, curr_season)

    # Iterate over the seasons
    for n in range(num_past_seasons):
        season_year = curr_season - n
        season_data = data["standings"][season_year]

        # Clean team names and create a DataFrame
        temp_df = pd.DataFrame.from_records(season_data)
        temp_df['team'] = [adjust_team_name(entry["team"]["name"]) for entry in season_data]
        temp_df['season'] = season_year

        # Filter teams to only those in the current season
        temp_df = temp_df[temp_df['team'].isin(team_list)]

        columns = [
            'season',
            'team',
            'position',
            'playedGames',
            'won',
            'draw',
            'lost',
            'points',
            'goalsFor',
            'goalsAgainst',
            'goalDifference',
        ]

        temp_df = temp_df[columns]
        standings_list.append(temp_df)

    # Combine all seasons into one DataFrame
    standings_df = pd.concat(standings_list, ignore_index=True)

    if show:
        print(standings_df)

    return standings_df

def get_fixtures(data: dict, season_year: int, show: bool = False):
    """
    Creates a DataFrame containing the fixtures (past and upcoming) for the specified season, in long format.
    """
    fixtures_list = []
    fixtures_data = data["matches"][season_year]

    for match in fixtures_data:
        matchday = match["matchday"]
        match_date = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
        status = match["status"]

        # Prepare data for home team
        home_team = adjust_team_name(match["homeTeam"]["name"])
        away_team = adjust_team_name(match["awayTeam"]["name"])
        score = match["score"]["fullTime"]

        fixture_home = {
            'season': season_year,
            'matchday': matchday,
            'team': home_team,
            'date': match_date,
            'atHome': True,
            'opponent': away_team,
            'status': status,
            'awayScore': score['away'],
            'homeScore': score['home'],
        }
        fixtures_list.append(fixture_home)

        # Prepare data for away team
        fixture_away = {
            'season': season_year,
            'matchday': matchday,
            'team': away_team,
            'date': match_date,
            'atHome': False,
            'opponent': home_team,
            'status': status,
            'awayScore': score['away'],
            'homeScore': score['home'],
        }
        fixtures_list.append(fixture_away)

    # Create DataFrame from list
    fixtures_df = pd.DataFrame(fixtures_list)

    if show:
        print(fixtures_df)

    return fixtures_df

def generate_season_weights(no_seasons: int):
    """Generates weightings for each season when computing the total rating."""
    factor = 2.5  # Higher value gives more weight to recent seasons
    weights = [0.01 * (factor ** (no_seasons - n - 1)) for n in range(no_seasons)]
    normalized_weights = np.array(weights) / sum(weights)
    return list(normalized_weights)

def calculate_team_ratings(standings_df: DataFrame, current_season: int, min_games_played: int, num_past_seasons: int = 3, show: bool = False):
    """
    Computes a DataFrame with each team's rating based on results from the past `num_past_seasons`.
    Includes 'current', 'prevSeasonN', and 'total' rating columns.

    Args:
        standings_df (DataFrame): DataFrame with standings data in long format.
        current_season (int): The current season's starting year.
        min_games_played (int): Minimum number of games played to include current season data.
        num_past_seasons (int, optional): Number of past seasons to include. Defaults to 3.
        show (bool, optional): If True, prints the resulting DataFrame. Defaults to False.

    Returns:
        DataFrame: A DataFrame with team ratings, including 'current', 'prevSeasonN', and 'total' columns.
    """
    # Filter standings_df to include only relevant seasons
    relevant_seasons = [current_season - n for n in range(num_past_seasons)]
    standings_filtered = standings_df[standings_df['season'].isin(relevant_seasons)]

    # Initialize the team_ratings DataFrame
    teams = standings_filtered['team'].unique()
    team_ratings = pd.DataFrame({'team': teams})
    team_ratings.set_index('team', inplace=True)

    # Calculate raw ratings for each team and season
    for n in range(num_past_seasons):
        season_year = current_season - n
        col_name = f"prevSeason{n}" if n > 0 else "current"
        season_data = standings_filtered[standings_filtered['season'] == season_year].copy()
        season_data['rating'] = season_data['points'] + season_data['goalDifference']
        season_ratings = season_data.set_index('team')['rating']
        team_ratings[col_name] = season_ratings

    # Replace NaNs with minimum rating in the column
    for col in team_ratings.columns:
        min_rating = team_ratings[col].min()
        team_ratings[col] = team_ratings[col].fillna(min_rating)

    # Normalize ratings per season
    for col in team_ratings.columns:
        max_rating = team_ratings[col].max()
        min_rating = team_ratings[col].min()
        if max_rating - min_rating != 0:
            team_ratings[col] = (team_ratings[col] - min_rating) / (max_rating - min_rating)
        else:
            team_ratings[col] = 0

    # Determine whether to include current season
    include_current = True
    current_season_games_played = standings_filtered[(standings_filtered['season'] == current_season)]['playedGames'].min()
    if current_season_games_played <= min_games_played:
        include_current = False
        logging.info("Team Ratings: Excluding current season from calculations due to insufficient games played.")
        team_ratings = team_ratings.drop(columns=['current'])
        num_past_seasons -= 1

    # Generate season weights
    weights = generate_season_weights(num_past_seasons)
    # Adjust weights if current season is excluded
    if not include_current:
        weights = generate_season_weights(num_past_seasons)
        seasons = [f"prevSeason{n}" for n in range(1, num_past_seasons + 1)]
    else:
        seasons = ['current'] + [f"prevSeason{n}" for n in range(1, num_past_seasons)]
    season_weights = dict(zip(seasons, weights))

    # Calculate total weighted rating
    team_ratings['total'] = 0
    for season_col in seasons:
        weight = season_weights[season_col]
        team_ratings['total'] += team_ratings[season_col] * weight

    # Sort by total rating
    team_ratings = team_ratings.sort_values(by='total', ascending=False)

    if show:
        print(team_ratings)

    # Reset index to have 'team' as a column
    team_ratings.reset_index(inplace=True)

    return team_ratings

def compute_home_advantages(data: dict, current_season: int, min_home_games: int, num_past_seasons: int = 3, show: bool = False):
    """
    Computes home advantage metrics for each team over the specified seasons, in long format.
    Includes detailed metrics per team per season, and calculates total home advantage per team.

    Args:
        data (dict): The JSON data containing fixtures.
        current_season (int): The current season's starting year.
        min_home_games (int): Minimum number of home games played to include a season's data.
        num_past_seasons (int, optional): Number of seasons to include. Defaults to 3.
        show (bool, optional): If True, prints the resulting DataFrame. Defaults to False.

    Returns:
        DataFrame: DataFrame containing home advantage metrics per team per season.
    """
    home_advantages_list = []
    relevant_seasons = [current_season - n for n in range(num_past_seasons)]

    for season_year in relevant_seasons:
        fixtures = data["matches"][season_year]
        team_stats = defaultdict(lambda: {
            'home_wins': 0,
            'home_draws': 0,
            'home_losses': 0,
            'away_wins': 0,
            'away_draws': 0,
            'away_losses': 0
        })

        for match in fixtures:
            if match["status"] != "FINISHED":
                continue

            home_team = adjust_team_name(match["homeTeam"]["name"])
            away_team = adjust_team_name(match["awayTeam"]["name"])
            home_goals = match["score"]["fullTime"]["home"]
            away_goals = match["score"]["fullTime"]["away"]

            if home_goals is None or away_goals is None:
                continue

            # Update stats based on match outcome
            if home_goals > away_goals:
                # Home team wins
                team_stats[home_team]['home_wins'] += 1
                team_stats[away_team]['away_losses'] += 1
            elif home_goals < away_goals:
                # Away team wins
                team_stats[home_team]['home_losses'] += 1
                team_stats[away_team]['away_wins'] += 1
            else:
                # Draw
                team_stats[home_team]['home_draws'] += 1
                team_stats[away_team]['away_draws'] += 1

        # Compute home advantage for each team in this season
        for team, stats in team_stats.items():
            home_played = stats['home_wins'] + stats['home_draws'] + stats['home_losses']
            away_played = stats['away_wins'] + stats['away_draws'] + stats['away_losses']
            total_played = home_played + away_played
            total_wins = stats['home_wins'] + stats['away_wins']

            if total_played == 0:
                continue  # Skip teams with no matches played

            home_win_ratio = stats['home_wins'] / home_played if home_played else 0
            overall_win_ratio = total_wins / total_played if total_played else 0
            home_advantage = home_win_ratio - overall_win_ratio

            home_advantages_list.append({
                'season': season_year,
                'team': team,
                'home_played': home_played,
                'home_winRatio': home_win_ratio,
                'overall_played': total_played,
                'overall_winRatio': overall_win_ratio,
                'homeAdvantage': home_advantage,
            })

    home_adv_df = pd.DataFrame(home_advantages_list)

    # Exclude seasons where teams have not played enough home games and exclude 2020 season
    filtered_home_adv_df = home_adv_df[
        (home_adv_df['home_played'] >= min_home_games) &
        (home_adv_df['season'] != 2020)
    ]

    # Exclude current season if teams have not played enough home games
    teams_to_exclude_current = home_adv_df.loc[
        (home_adv_df['season'] == current_season) & (home_adv_df['home_played'] < min_home_games), 'team'
    ].unique()
    # Remove current season data for these teams
    filtered_home_adv_df = filtered_home_adv_df[
        ~((filtered_home_adv_df['team'].isin(teams_to_exclude_current)) & (filtered_home_adv_df['season'] == current_season))
    ]

    # Compute totalHomeAdvantage per team
    total_home_advantage = filtered_home_adv_df.groupby('team')['homeAdvantage'].mean().reset_index()
    total_home_advantage.rename(columns={'homeAdvantage': 'totalHomeAdvantage'}, inplace=True)

    # Merge totalHomeAdvantage back into the main DataFrame
    home_adv_df = home_adv_df.merge(total_home_advantage, on='team', how='left')

    # Select and arrange columns as per requirement
    home_adv_df = home_adv_df[[
        'team',
        'season',
        'home_played',
        'home_winRatio',
        'homeAdvantage',
        'overall_played',
        'overall_winRatio',
        'totalHomeAdvantage'
    ]]

    # Sort by team's total home advantage
    home_adv_df = home_adv_df.sort_values(by='totalHomeAdvantage', ascending=False)

    if show:
        print(home_adv_df)

    return home_adv_df



def compute_form(data: dict, team_ratings_df: DataFrame, season_year: int, num_past_seasons: int = 2, show: bool = False):
    """
    Builds a DataFrame containing the form data for each team over the current and past seasons, in long format.
    """
    form_records = []
    all_teams = set()

    team_data = {}
    for i in range(num_past_seasons):
        season = season_year - i
        fixtures = data["matches"][season]

        # Collect all teams
        teams_in_season = set()
        for match in fixtures:
            home_team = adjust_team_name(match["homeTeam"]["name"])
            away_team = adjust_team_name(match["awayTeam"]["name"])
            teams_in_season.update([home_team, away_team])
        all_teams.update(teams_in_season)


        # Sort matches by date
        fixtures = sorted(fixtures, key=lambda x: x["utcDate"])

        for match in fixtures:
            if match["status"] != "FINISHED":
                continue

            matchday = match["matchday"]
            match_date = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
            home_team = adjust_team_name(match["homeTeam"]["name"])
            away_team = adjust_team_name(match["awayTeam"]["name"])
            score = match["score"]["fullTime"]
            home_team_tla = match["homeTeam"].get("tla", "".join([word[0] for word in home_team.split()]))
            away_team_tla = match["awayTeam"].get("tla", "".join([word[0] for word in away_team.split()]))

            # Process home team
            process_form_entry(team_data, team_ratings_df, season, matchday, match_date, home_team, away_team, True, score, home_team_tla, away_team_tla)

            # Process away team
            process_form_entry(team_data, team_ratings_df, season, matchday, match_date, away_team, home_team, False, score, away_team_tla, home_team_tla)

        # Calculate positions per matchday
        for matchday in range(1, max([match['matchday'] for match in fixtures]) + 1):
            # Collect cumulative points and goal difference up to this matchday
            standings = []
            for team in team_data.keys():
                # Get last entry up to this matchday
                entries = [entry for entry in team_data[team] if entry['matchday'] <= matchday]
                if entries:
                    last_entry = entries[-1]
                    standings.append({
                        'team': team,
                        'cumPoints': last_entry['cumPoints'],
                        'cumGD': last_entry['cumGD'],
                        'matchday': matchday
                    })
                else:
                    # If no entries yet, default to zero
                    standings.append({
                        'team': team,
                        'cumPoints': 0,
                        'cumGD': 0,
                        'matchday': matchday
                    })

            # Sort standings
            standings_sorted = sorted(standings, key=lambda x: (-x['cumPoints'], -x['cumGD']))
            # Assign positions
            for idx, item in enumerate(standings_sorted, start=1):
                team = item['team']
                matchday = item['matchday']
                # Find the entry for this team at this matchday
                entries = [entry for entry in team_data[team] if entry['matchday'] == matchday]
                if entries:
                    entry = entries[-1]
                    entry['position'] = idx
                else:
                    # If the team did not play this matchday, we need to create an entry
                    entry = {
                        'season': season,
                        'matchday': matchday,
                        'team': team,
                        'date': None,
                        'opponent': None,
                        'score': None,
                        'gD': 0,
                        'points': 0,
                        'cumPoints': item['cumPoints'],
                        'cumGD': item['cumGD'],
                        'form5': '',
                        'form10': '',
                        'formRating5': None,
                        'formRating10': None,
                        'position': idx,
                        'atHome': None,
                        "result": None,
                        'team_tla': None,
                        'opponent_tla': None

                    }
                    team_data[team].append(entry)

    # Collect records from team_data
    for team_entries in team_data.values():
        form_records.extend(team_entries)

    # Create DataFrame
    form_df = pd.DataFrame.from_records(form_records)

    # Ensure columns are in desired order
    desired_columns = [
        'season', 'matchday', 'team', 'date', 'opponent', 'score',
        'gD', 'points', 'position', 'form5', 'form10',
        'formRating5', 'formRating10', 'cumGD', 'cumPoints', 'atHome', 'result',"team_tla", "opponent_tla"
    ]
    form_df = form_df[desired_columns]

    # Sort by season, matchday, team
    form_df.sort_values(by=['season', 'matchday', 'team'], inplace=True)

    if show:
        print(form_df)

    return form_df

def process_form_entry(team_data, team_ratings_df: DataFrame, season: int, matchday: int, match_date: datetime,
                       team: str, opponent: str, at_home: bool, score: dict, team_tla: str, opponent_tla: str):
    """Processes form data for a single team and match."""
    # Initialize team data if not present
    if team not in team_data:
        team_data[team] = []

    # Calculate goal difference and points
    goal_diff = calculate_goal_difference(score, at_home)
    points = calculate_points(goal_diff)
    result_char = get_result_char(goal_diff)

    # Update cumulative stats
    if team_data[team]:
        cum_points = team_data[team][-1]['cumPoints'] + points
        cum_gd = team_data[team][-1]['cumGD'] + goal_diff
        prev_form5 = team_data[team][-1]['form5']
        prev_form10 = team_data[team][-1]['form10']
    else:
        cum_points = points
        cum_gd = goal_diff
        prev_form5 = ''
        prev_form10 = ''

    # Update form strings
    form5_str = (prev_form5 + result_char)[-5:]
    form10_str = (prev_form10 + result_char)[-10:]

    # Calculate form ratings
    form_rating5 = calc_form_rating(team_ratings_df, [opponent], form5_str, [goal_diff], season)
    form_rating10 = calc_form_rating(team_ratings_df, [opponent], form10_str, [goal_diff], season)

    entry = {
        'season': season,
        'matchday': matchday,
        'team': team,
        'date': match_date,
        'opponent': opponent,
        'score': f"{score['home']}-{score['away']}" if at_home else f"{score['away']}-{score['home']}",
        'gD': goal_diff,
        'points': points,
        'cumPoints': cum_points,
        'cumGD': cum_gd,
        'form5': form5_str,
        'form10': form10_str,
        'formRating5': form_rating5,
        'formRating10': form_rating10,
        'atHome': at_home,
        'result': result_char,
        'team_tla': team_tla,
        'opponent_tla': opponent_tla,
        # 'position': will be added later
    }
    team_data[team].append(entry)

def calc_form_rating(team_ratings_df: DataFrame, teams_played: list, form_str: str, gds: list, season: int):
    """Calculates form rating based on recent matches and opponent ratings."""
    form_rating = 0.5  # Default percentage, moves up or down based on performance

    if not form_str:
        return form_rating
    for team_data in team_ratings_df.to_dict(orient='records'):
        if team_data["team"] in teams_played:
            opposition_rating = team_data["total"]
            form_rating += (opposition_rating / len(form_str)) * gds[0]
    
    form_rating = min(max(0, form_rating), 1)  # Cap rating
    return form_rating

def calculate_goal_difference(score: dict, is_home: bool):
    """Calculates goal difference based on the score and whether the team was at home."""
    if score['home'] is None or score['away'] is None:
        return 0
    if is_home:
        return score["home"] - score["away"]
    else:
        return score["away"] - score["home"]

def calculate_points(goal_diff: int):
    """Calculates points earned based on goal difference."""
    if goal_diff > 0:
        return 3
    elif goal_diff == 0:
        return 1
    else:
        return 0

def get_result_char(goal_diff: int):
    """Returns a character representing the match result."""
    if goal_diff > 0:
        return "W"
    elif goal_diff < 0:
        return "L"
    else:
        return "D"

def find_next_fixture(fixtures_df: DataFrame, team: str):
    """Finds the next scheduled fixture for the specified team."""
    now = datetime.now()
    future_fixtures = fixtures_df[(fixtures_df['team'] == team) & (fixtures_df['status'] == 'SCHEDULED') & (fixtures_df['date'] > now)]
    if future_fixtures.empty:
        return None, None, None
    next_fixture = future_fixtures.sort_values('date').iloc[0]
    return next_fixture['date'], next_fixture['opponent'], next_fixture['atHome']

def prepare_upcoming_fixtures(data: dict, fixtures_df: DataFrame, season_year: int, num_past_seasons: int = 2, show: bool = False):
    """
    Creates a DataFrame detailing the next fixture for each team, including previous matches against the upcoming opponent.
    """
    teams = fixtures_df['team'].unique()
    upcoming_fixtures_list = []

    for team in teams:
        next_date, next_opponent, at_home = find_next_fixture(fixtures_df, team)
        if next_date is None:
            continue  # No upcoming fixture
        # Get previous matches between team and next_opponent
        prev_matches = []
        for i in range(num_past_seasons):
            season = season_year - i
            season_fixtures = data['matches'][season]
            for match in season_fixtures:
                if match['status'] != 'FINISHED':
                    continue
                match_teams = [adjust_team_name(match["homeTeam"]["name"]), adjust_team_name(match["awayTeam"]["name"])]
                if team in match_teams and next_opponent in match_teams:
                    match_date = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
                    home_team = adjust_team_name(match["homeTeam"]["name"])
                    away_team = adjust_team_name(match["awayTeam"]["name"])
                    home_goals = match["score"]["fullTime"]["home"]
                    away_goals = match["score"]["fullTime"]["away"]
                    scoreline = f"{home_goals}-{away_goals}"
                    prev_matches.append({
                        'date': match_date,
                        'homeTeam': home_team,
                        'awayTeam': away_team,
                        'score': scoreline
                    })
        # Sort previous matches by date
        prev_matches.sort(key=lambda x: x['date'], reverse=True)

        upcoming_fixtures_list.append({
            'team': team,
            'date': next_date,
            'opponent': next_opponent,
            'isHome': at_home,
            'previousMatches': prev_matches
        })

    upcoming_df = pd.DataFrame(upcoming_fixtures_list)

    if show:
        print(upcoming_df)

    return upcoming_df

def save_to_json(df, file_name):
    """Saves a DataFrame to a JSON file, ensuring data is JSON serializable."""
    df_copy = df.copy()
    # Convert datetime objects to strings
    for col in df_copy.select_dtypes(include=['datetime', 'datetime64[ns]']).columns:
        df_copy[col] = df_copy[col].astype(str)

    # Convert any columns with dictionaries or lists to JSON strings
    for col in df_copy.columns:
        if df_copy[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_copy[col] = df_copy[col].apply(lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list)) else x)

    df_copy = df_copy.replace({np.nan: None})
    df_copy.to_json(file_name, orient='records', indent=2)



# Example usage
def update_data(update:bool=False, LEAGUE:str=None, CURRENT_SEASON:int=None):
    if LEAGUE is None:
        LEAGUE = os.getenv('LEAGUE')
    if CURRENT_SEASON is None:
        CURRENT_SEASON = int(os.getenv('CURRENT_SEASON'))

    data = fetch_all_data(
        league=LEAGUE,
        current_season=CURRENT_SEASON,
        fetch_again=update
    )

    standings_df = get_standings(data, CURRENT_SEASON, show=False)
    standings_df["league"]=LEAGUE
    fixtures_df = get_fixtures(data, CURRENT_SEASON, show=False)
    fixtures_df["league"]=LEAGUE
    team_ratings_df = calculate_team_ratings(standings_df, CURRENT_SEASON, min_games_played=4, num_past_seasons=2, show=False)
    team_ratings_df["league"]=LEAGUE
    home_adv_df = compute_home_advantages(data, CURRENT_SEASON, min_home_games=4, num_past_seasons=2, show=False)
    home_adv_df["league"]=LEAGUE
    form_df = compute_form(data, team_ratings_df, CURRENT_SEASON, num_past_seasons=2, show=False)
    form_df["league"]=LEAGUE
    upcoming_df = prepare_upcoming_fixtures(data, fixtures_df, CURRENT_SEASON, num_past_seasons=2, show=False)
    upcoming_df["league"]=LEAGUE

    # Connect to DuckDB database
    

    if update:
        # Save DataFrames to DuckDB
        save_to_duckdb(standings_df, 'standings')
        save_to_duckdb(fixtures_df, 'fixtures')
        save_to_duckdb(team_ratings_df, 'team_ratings')
        save_to_duckdb(home_adv_df, 'home_advantages')
        save_to_duckdb(form_df, 'form')
        save_to_duckdb(upcoming_df, 'upcoming')
        save_last_updated_time(LEAGUE)
        print("Data updated successfully!")
        print(cal_time_passed(LEAGUE))
        # Save DataFrames to JSON files
        save_to_json(standings_df, 'standings.json')
        save_to_json(fixtures_df, 'fixtures.json')
        save_to_json(team_ratings_df, 'team_ratings.json')
        save_to_json(home_adv_df, 'home_advantages.json')
        save_to_json(form_df, 'form.json')
        save_to_json(upcoming_df, 'upcoming.json')


if __name__ == "__main__":
    update_data(False, "PD", 2024)
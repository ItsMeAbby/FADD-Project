import dash
from dash import html
import pandas as pd

# Helper functions to compute statistics
def calculate_stats(form_df, team):
    team_data = form_df[form_df['team'] == team]
    overall_data = form_df

    # Compute statistics for all teams
    teams_stats = []
    for t in form_df['team'].unique():
      team_df = form_df[form_df['team'] == t]
      total_games = len(team_df.dropna(subset=['score']))
      # Calculate goals scored using row-wise logic based on atHome flag
      goals_scored = team_df.dropna(subset=['score']).apply(
        lambda row: int(row['score'].split('-')[0]),
        axis=1
      ).sum()
      # Calculate goals conceded similarly
      goals_conceded = team_df.dropna(subset=['score']).apply(
        lambda row: int(row['score'].split('-')[1]),
        axis=1
      ).sum()
      # Count clean sheets: either a '0-0' result or the team kept a clean sheet at home/away
      clean_sheets = team_df.dropna(subset=['score']).apply(
        lambda row: 1 if (row['score'] == '0-0' or 
                  row['score'].split('-')[1] == '0')
              else 0,
        axis=1
      ).sum()
      teams_stats.append({
        'total_games': int(total_games),
        'goals_scored': int(goals_scored),
        'goals_conceded': int(goals_conceded),
        'clean_sheets': int(clean_sheets),
        'avg_goals_scored': float(goals_scored / total_games),
        'avg_goals_conceded': float(goals_conceded / total_games),
        'clean_sheet_ratio': float(clean_sheets / total_games),
        "team": t
      })
    stats_df=pd.DataFrame(teams_stats)
    # Compute ranks for each statistic
    # xG rank: goals scored
    stats_df['xG_rank'] = stats_df['avg_goals_scored'].rank(ascending=False)
    # xC rank: goals conceded
    stats_df['xC_rank'] = stats_df['avg_goals_conceded'].rank()
    # Clean sheet rank
    stats_df['clean_sheet_rank'] = stats_df['clean_sheet_ratio'].rank(ascending=False)

    # Get the statistics for the selected team
    selected_team_stats = stats_df[stats_df['team'] == team].iloc[0]
    return selected_team_stats.to_dict()
    
    
    


# Sample ordinal function to convert rank
def ordinal(n):
    SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = SUFFIXES.get(n % 10, 'th')
    return str(n) + suffix

def update_team_stats(selected_team, form_df):
    stats = calculate_stats(form_df, selected_team)
    return html.Div(className="season-stats", children=[
        html.Div(className="season-stat goals-per-game", children=[
            html.Div(className="season-stat-value", children=[
                html.Span(className="season-stat-number", children=f"{stats['avg_goals_scored']:.2f}"),
                html.Span(className="season-stat-position", children=ordinal(int(stats['xG_rank'])))
            ]),
            html.Div(className="season-stat-text", children="Goals per Game")
        ]),
        html.Div(className="season-stat conceded-per-game", children=[
            html.Div(className="season-stat-value", children=[
                html.Span(className="season-stat-number", children=f"{stats['avg_goals_conceded']:.2f}"),
                html.Span(className="season-stat-position", children=ordinal(int(stats['xC_rank'])))
            ]),
            html.Div(className="season-stat-text", children="Conceded per Game")
        ]),
        html.Div(className="season-stat clean-sheet-ratio", children=[
            html.Div(className="season-stat-value", children=[
                html.Span(className="season-stat-number", children=f"{stats['clean_sheet_ratio']:.2f}"),
                html.Span(className="season-stat-position", children=ordinal(int(stats['clean_sheet_rank'])))
            ]),
            html.Div(className="season-stat-text", children="Clean Sheets")
        ]),
    ])

    

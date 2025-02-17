from dash import html
import pandas as pd

from dash import html
import pandas as pd
from utils.constants import clean_names,team_colors

def build_next_game_component(upcoming_df, standings_df, form_df, team):
    next_game = get_next_game(upcoming_df, team)
    if next_game is None or pd.isnull(next_game['opponent']):
        return html.Div("Season Complete!", style={'textAlign': 'center', 'fontSize': '2em'})
    
    opponent = next_game['opponent']
    at_home = next_game['isHome']
    opponent_position = get_opponent_position(standings_df, opponent)
    opponent_form_percentage = calculate_form_percentage(form_df, opponent)
    previous_matches = get_previous_matches(upcoming_df, team, opponent)
    
    header_style = {
        'backgroundColor': '#280936',
        'padding': '24px',
        'borderTopLeftRadius': '8px',
        'borderTopRightRadius': '8px',
        'marginBottom': '20px'
    }
    
    title_style = {
        'color': 'white',
        'fontSize': '32px',
        'fontWeight': 'bold',
        'display': 'flex',
        'alignItems': 'center',
        'gap': '8px'
    }
    
    content_container = {
        'display': 'flex',
        'justifyContent': 'space-between',
        'padding': '32px',
        'alignItems': 'flex-start'
    }
    
    stats_container = {
        'textAlign': 'center',
        'flex': '1'
    }
    
    position_style = {
        'fontSize': '100px',
        'fontWeight': 'bold',
        'color': '#280936',
        'lineHeight': '1',
        'marginBottom': '24px'
    }
    
    form_style = {
        'marginTop': '16px',
        'fontSize': 'px',
        'padding': '9px 0',
        'background': '#280936', 
        'borderRadius': '6px', 
        'textAlign': 'center'
    }
    
    results_container = {
        'flex': '1',
        'paddingLeft': '32px'
    }
    
    result_row_style = {
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'marginBottom': '8px'
    }
    
    score_box_style = {
        'backgroundColor': '#dc2626',
        'color': 'white',
        'padding': '4px 24px',
        'borderRadius': '4px',
        'margin': '0 8px'
    }
    
    def build_result_row(match):
        home_score = match['score'].split('-')[0].strip()
        away_score = match['score'].split('-')[1].strip()
        date = match['date'].strftime('%d %b %Y')
        home_team_color = team_colors.get(match['home_team'],{}).get('primary', '#000')
        home_team_color_secondary = team_colors.get(match['home_team'],{}).get('secondary', '#000')
        away_team_color = team_colors.get(match['away_team'],{}).get('primary', '#000')
        away_team_color_secondary = team_colors.get(match['away_team'],{}).get('secondary', '#000')
        left_color=home_team_color
        left_color_secondary=home_team_color_secondary
        right_color=away_team_color
        right_color_secondary=away_team_color_secondary

        if home_score > away_score:
            right_color=left_color
            right_color_secondary=left_color_secondary
        elif home_score < away_score:
            left_color=right_color
            left_color_secondary=right_color_secondary
        
        return html.Div([
            html.Div(date, style={'fontSize': '14px', 'marginBottom': '4px', 'textAlign': 'center',"fontWeight": "bold"}),
            html.Div(
                [
                    html.Div(clean_names.get(match['home_team'], match["home_team"]), 
                    style={'backgroundColor': home_team_color, 'color': home_team_color_secondary, 'padding': '4px 12px', 'borderRadius': '4px 0 0 4px', 'width': '30%', 'textAlign': 'left'}),
                    
                    html.Div([f"{home_score}"], 
                    style={'backgroundColor': left_color, 'color': left_color_secondary, 'padding': '4px 12px', 'margin': '-8px 0', 'flex': '1', 'textAlign': 'center' , 'width': '20%', "borderRight": '1px solid #280936', "textAlign": "right"}),

                    html.Div([f"{away_score}"],
                    style={'backgroundColor': right_color, 'color': right_color_secondary, 'padding': '4px 12px', 'margin': '-8px 0', 'flex': '1', 'textAlign': 'center' , 'width': '20%', "borderLeft": '1px solid #280936', "textAlign": "left"}),

                    html.Div(clean_names.get(match['away_team'], match["away_team"]),
                    style={'backgroundColor': away_team_color, 'color': away_team_color_secondary, 'padding': '4px 12px', 'borderRadius': '0 4px 4px 0', 'width': '30%', 'textAlign': 'right'}),
                ],
                style={'display': 'flex', 'alignItems': 'center'})
        ], style={'marginBottom': '12px'})
    
    return html.Div([
        # Header
        html.Div([
            html.Div([
                "Next Game: ",
                html.Span(clean_names.get(opponent,opponent), style={'color': '#00ff9d'}),
                f" ({'Home' if at_home else 'Away'})"
            ], style=title_style)
        ], style=header_style),
        
        # Content
        html.Div([
            # Left side - Stats
            html.Div([
                html.Div([
                    f"{opponent_position}",
                    html.Span(get_ordinal_suffix(int(opponent_position)), style={'fontSize': '32px', 'verticalAlign': 'top'})
                ], style=position_style),
                html.Div([
                    html.Span("Current form: ", style={'color': 'white'}),
                    html.Span(f"{opponent_form_percentage}", style={'color': '#00ff00', 'fontWeight': 'bold'})
                ], style=form_style),
            ], style=stats_container),
            
            # Right side - Previous Results
            html.Div([
                html.H3("Previous results", style={'fontSize': '20px', 'fontWeight': 'bold', 'marginBottom': '16px'}),
                html.Div([
                    build_result_row(match) for match in previous_matches
                ])
            ], style=results_container)
        ], style=content_container)
    ], style={
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'height': '100%',
        'border': '2px solid #280936'
    })
def get_ordinal_suffix(number):
    if number % 100 in [11, 12, 13]:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
    return suffix
def get_next_game(upcoming_df, team):
    next_game_row = upcoming_df[upcoming_df['team'] == team]
    if next_game_row.empty:
        return None
    return next_game_row.iloc[0]

def get_opponent_position(standings_df, opponent):
    opponent_standing = standings_df[standings_df['team'] == opponent]
    return opponent_standing.iloc[0]['position'] if not opponent_standing.empty else 'N/A'

def calculate_form_percentage(form_df, team):
    team_form_data = form_df[form_df['team'] == team].sort_values('matchday', ascending=False)
    team_form_data = team_form_data[team_form_data['score'].notnull()].head(5)
    if not team_form_data.empty and pd.notnull(team_form_data.iloc[0]['formRating5']):
        form_rating = team_form_data.iloc[0]['formRating5'] * 100
        return f"{form_rating:.1f}%"
    return 'N/A'

def get_previous_matches(upcoming_df, team, opponent):
    next_game_row = upcoming_df[upcoming_df['team'] == team]
    if next_game_row.empty:
        return []
    previous_matches_str = next_game_row.iloc[0]['previousMatches']
    if isinstance(previous_matches_str, float) and previous_matches_str == 0.0:  # Handling NaN or empty array.
        return []
    return [
        {
            'date': pd.to_datetime(match['date']),
            'home_team': match['homeTeam'],
            'away_team': match['awayTeam'],
            'score': match['score']
        } for match in previous_matches_str
    ]

def build_previous_matches_divs(previous_matches):
    return [
        html.Div([
            html.Div(match['date'].strftime('%d %b %Y'), style={'width': '30%'}),
            html.Div(f"{match['home_team']} {match['score']} {match['away_team']}", style={'width': '70%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': '5px 0'})
        for match in previous_matches
    ]
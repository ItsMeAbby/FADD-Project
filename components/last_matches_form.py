from dash import html
import pandas as pd

def display_current_form(form_df, team):
    form_icons, star_teams, opponent_initials = get_team_form(form_df, team)
    form_tiles = create_form_tiles(form_icons, star_teams)
    opponent_initials_divs = [
        html.Div(opponent_initials[i], style={
            'position': 'relative',
            'marginTop': '0.6em',
            'textAlign': 'center',
            'flex': '1'
        }) for i in range(5)
    ]
    form_percentage = calculate_form_percentage(form_df, team)
    return html.Div([
        html.Div(form_tiles, style={'display': 'flex', 'marginTop': '10px', 'justifyContent': 'center'}),
        html.Div(opponent_initials_divs, style={'display': 'flex', 'justifyContent': 'center'}),
        html.Div([
            html.Span("Current form: ", style={'color': 'white'}),
            html.Span(form_percentage, style={'color': '#00ff00'})
        ], style={
            'fontSize': '1.7rem', 
            'margin': '20px 0', 
            'width': '100%', 
            'padding': '9px 0',
            'background': '#280936', 
            'borderRadius': '6px', 
            'textAlign': 'center',
            "fontWeight": "bold"
        })
    ])

def get_team_form(form_df, team):
    team_form_data = form_df[form_df['team'] == team].sort_values('matchday', ascending=False)
    team_form_data = team_form_data[team_form_data['score'].notnull()].head(5)

    results = []
    star_teams = []
    opponent_initials = []
    for _, row in team_form_data.iterrows():
        results.append(row["result"])
        opponent = row['opponent']
        rating_row = team_form_data[team_form_data['team'] == opponent]
        is_star_team = False
        if not rating_row.empty and rating_row.iloc[0]['total'] > 0.75:
            is_star_team = True
        star_teams.append(is_star_team)
        opponent_initials.append(row["opponent_tla"])
    while len(results) < 5:
        results.append('')
        star_teams.append(False)
        opponent_initials.append('')
    return results[::-1], star_teams[::-1], opponent_initials[::-1]

def create_form_tiles(form, star_teams):
    tiles = []
    for i, result in enumerate(form):
        background = get_background_color(result, star_teams[i])
        tile_style = {
            'background': background,
            'width': '100%',
            'aspectRatio': '1 / 0.8',
            'color': '#2b2d2f',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'borderRadius': 'inherit',
            'flex': '1',
            # light grey border
            "border": "0.25px solid #d6d6d6",
        }
        if i == 0:
            tile_style['borderRadius'] = '6px 0 0 6px'
        elif i == 4:
            tile_style['borderRadius'] = '0 6px 6px 0'
        tile = html.Div(
            children=html.Div(
                children=result if result in ['W', 'D', 'L'] else '',
                style={'fontSize': '2vw', 'marginTop': '0.14em'},
                className='result'
            ),
            style=tile_style,
        )
        tiles.append(tile)
    return tiles

def get_background_color(result, star_team):
    if result == 'W':
        return 'linear-gradient(30deg, green, #2bd2ff, #fa8bff)' if star_team else '#00ff00'
    if result == 'D':
        return '#ffcc00'
    if result == 'L':
        return '#f5271d'
    return '#d6d6d6'

def calculate_form_percentage(form_df:pd.DataFrame, team):
    team_form_data = form_df[form_df['team'] == team].sort_values('matchday', ascending=False)
    team_form_data = team_form_data[team_form_data['score'].notnull()].head(5)
    if not team_form_data.empty and pd.notnull(team_form_data.iloc[0]['formRating5']):
        form_rating = team_form_data.iloc[0]['formRating5'] * 100
        return f"{form_rating:.1f}%"
    return 'N/A'
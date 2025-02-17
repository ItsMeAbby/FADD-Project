from dash import html
from utils.constants import clean_names
LEFT_PANEL_STYLE = {
    'width': '15%',
    'display': 'inline-block',
    'verticalAlign': 'top',
    'position': 'fixed',
    'height': '100vh',
    'overflowY': 'auto',
    'backgroundColor': '#280936',
    'padding': '0px',
    'boxSizing': 'border-box',
    'overflowX': 'hidden',
    'scrollbarWidth': 'none',
    
}

RIGHT_PANEL_STYLE = {
    'width': '85%',
    'display': 'inline-block',
    'marginLeft': '15%',
    'padding': '0px',
    'boxSizing': 'border-box'
}

def build_team_list(teams):
    return html.Div(id='left-panel', children=[
        html.H2('DASHBOARD', style={'textAlign': 'center', "color": "white", "padding": "20px","marginBottom": "10px"}),
        html.Ul(id='team-list', children=[
            html.Li(
                html.Button(
                    clean_names.get(team, team),
                    id={'type': 'team-button', 'index': team},
                    n_clicks=0,
                    className="team-button",  # Add CSS class for hover effects
                    style={
                        'width': '100%',
                        'padding': '7px 6px 7px 20px',
                        'textAlign': 'left',
                        'border': 'none',
                        'cursor': 'pointer',
                        'backgroundColor': 'transparent',
                        'color': '#c600d8',
                        'fontWeight': 'bold'
                        
                    }
                )
            ) for team in teams
        ], style={'listStyleType': 'none', 'border': 'none', 'padding': '0px', 'margin': '0px', 'fontSize': '1em'})
    ])
import json
import os
import dash
from dash import html, dcc, Output, Input, State
from utils.db import load_data,cal_time_passed
from layout import *
from components.fixture_plot import build_fixture_plot_data
from components.last_matches_form import display_current_form
from components.standings_table import build_table_snippet
from components.next_game_component import build_next_game_component
from utils.constants import team_colors
from components.form_plot import build_form_time_plot
from components.position_plot import build_position_time_plot
from components.points_plot import build_points_time_plot
from components.cleansheet_plot import create_clean_sheets_figure
from components.goals_per_matchday_plot import build_goals_per_game_barchart
from components.stats_labels import update_team_stats
from components.league_position import get_position
from utils.data_loader import update_data
# Load the data
from dotenv import load_dotenv
load_dotenv(override=True)

league = os.getenv("LEAGUE")
current_season = int(os.getenv("CURRENT_SEASON"))
if cal_time_passed(league) > 5:
    print("Data is stale",cal_time_passed(league))
    update_data(update=True,LEAGUE=league,CURRENT_SEASON=current_season)
    

standings_df, fixtures_df, form_df, team_ratings_df, home_advantages_df, upcoming_df = load_data(league, current_season)
teams = standings_df['team'].unique()

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Dashboard"

# Build the app layout
app.layout = html.Div([
    html.Div(build_team_list(teams), style=LEFT_PANEL_STYLE),
    html.Div(id='right-panel', children=[
        html.H1(id='team-header', style={'textAlign': 'center'}),
        html.Div(id='content', children=[], style={'display': 'flex'})
    ], style=RIGHT_PANEL_STYLE)
])

def determine_team(n_clicks_list, teams):
    ctx = dash.callback_context
    if not ctx.triggered:
        return teams[0]
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # It is assumed that the IDs were created from a dictionary so eval() helps retrieve the index key.
    return eval(button_id)['index']

# Merged callback to update team header, content, and button styles.
@app.callback(
    [Output('team-header', 'children'),
     Output('team-header', 'style'),
     Output('content', 'children'),
     Output({'type': 'team-button', 'index': dash.dependencies.ALL}, 'style')],
    [Input({'type': 'team-button', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('content', 'children'),
     State({'type': 'team-button', 'index': dash.dependencies.ALL}, 'id')]
)
def update_all(n_clicks_list, current_content, button_ids):
    # Determine the selected team:
    selected_team = determine_team(n_clicks_list, teams)
    team_color = team_colors.get(selected_team, {'primary': 'red', 'secondary': 'black'})

    # Build the fixture plot and retrieve the league position:
    fig = build_fixture_plot_data(fixtures_df, team_ratings_df, home_advantages_df, selected_team)
    fixture_plot_div = html.Div([
        html.H1("Fixtures", 
                style={'textAlign': 'center', 'fontSize': '2rem', 'margin': '10px'}),
        html.Div(
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False,
            'showSendToCloud': False}
            ),
            style={'flex': '1'}
        )
    ], className="row-right fixtures-graph", 
       style={'flex': '10', 'padding': '10px'})
    position = standings_df.loc[standings_df['team'] == selected_team, 'position'].squeeze()

    # League Position Design
    league_position_div = get_position(position, team_color)


    # Top Section
    leage_fixture_section = html.Div([
        html.Div([league_position_div], style={'width': '35%', 'padding': '10px'}),
        fixture_plot_div
    ], style={
        'display': 'flex'
    })

    # Form and Table
    form_table_div = html.Div([
        html.Div(display_current_form(form_df, selected_team), style={'width': '100%', 'marginTop': '20px'}),
        html.Div(build_table_snippet(standings_df, selected_team), style={'width': '100%', 'marginTop': '20px'})
    ], style={'width': '35%', 'padding': '10px'})

    # Next Game Component
    next_game_div = html.Div([build_next_game_component(upcoming_df, standings_df, form_df, selected_team)
    ], style={'width': '65%','padding': '10px', 'borderRadius': '6px', "height": "100%",
        'minHeight' : '100%'})

    # Bottom Section
    form_game_section = html.Div([
        form_table_div, next_game_div
    ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%'})

    form_plot_section = build_form_time_plot(form_df, selected_team)
    position_plot_section = build_position_time_plot(form_df, selected_team)
    points_plot_section = build_points_time_plot(form_df, selected_team)
    build_goals_per_game_barchart_section = build_goals_per_game_barchart(form_df, selected_team)
    # Combine all sections into content
    stats_section= update_team_stats(selected_team,form_df)
    content = html.Div([
        leage_fixture_section, 
        form_game_section,
        form_plot_section,
        position_plot_section,
        points_plot_section,
        stats_section,
        build_goals_per_game_barchart_section,
        ],
                       style={'width': '100%',"paddingBottom": "20px"})
    team_header_style = {
        'textAlign': 'center',
        'backgroundColor': team_color['primary'],
        'color': team_color['secondary'],
        'padding': '20px',
        'fontSize': '2em'
    }

    # Now, update button styles for all team buttons based on whether they are selected.
    new_button_styles = []
    for comp_id in button_ids:
        if comp_id['index'] == selected_team:
            tc = team_colors.get(comp_id['index'], {'primary': '#c600d8', 'secondary': '#000'})
            style = {
                'width': '100%',
                'padding': '7px 7px 7px 20px',
                'textAlign': 'left',
                'border': 'none',
                'cursor': 'pointer',
                'backgroundColor': tc['primary'],
                'color': tc['secondary'],
                'fontWeight': 'bold'
            }
        else:
            style = {
                'width': '100%',
                'padding': '7px 7px 7px 20px',
                'textAlign': 'left',
                'border': 'none',
                'cursor': 'pointer',
                'backgroundColor': 'transparent',
                'color': '#c600d8',
                'fontWeight': 'bold'
            }
        new_button_styles.append(style)

    # Return all outputs at once.
    return selected_team, team_header_style, content, new_button_styles

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
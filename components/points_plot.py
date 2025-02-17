import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
from utils.constants import clean_names, team_colors

def get_points_line(form_df, team, is_main_team):
    """Creates a single team's form rating line for the plot"""
    
    team_df = form_df[form_df['team'] == team].copy()
    # convert date to strf
    team_df['date'] = team_df['date'].dt.strftime('%Y %b %d')

    if team_df.empty:
        return None  # Skip if no data
    
    line_color = team_colors.get(team, {'primary': '#c600d8', 'secondary': '#000'})['primary'] if is_main_team else '#d3d3d3'

    return go.Scatter(
        x=team_df['matchday'],
        y=team_df['cumPoints'],
        mode='lines',
        line=dict(color=line_color, width=4 if is_main_team else 2),
        text=team_df['date'].astype(str),
        customdata=team_df[['team']],
        hovertemplate="<b>%{customdata[0]}</b><br>Matchday %{x}<br>%{text}<br>Points: <b>%{y}</b><extra></extra>",
        showlegend=False  # Hide legend
    )

def build_points_time_plot(form_df, selected_team):
    """Generates the full form rating plot for all teams"""

    # Clean data
    form_df = form_df.copy()
    form_df['team'] = form_df['team']
    # drop na values whre score is null
    form_df = form_df.dropna(subset=['score'])
    form_df['date'] = pd.to_datetime(form_df['date'])
    form_df['matchday'] = form_df['matchday'].astype(int)

    # Create traces for all teams
    teams = form_df['team'].unique()
    traces = [get_points_line(form_df, team, team == selected_team) for team in teams if team != selected_team]
    traces.append(get_points_line(form_df, selected_team, True))
    traces = [trace for trace in traces if trace]  # Remove None values

    # Set y-axis labels (0 to 100 in steps of 10)
    y_labels = list(range(0, max(form_df['cumPoints']) + 1, 5))

    fig = go.Figure(traces)
    fig.update_layout(
        autosize=True,
        margin=dict(r=20, l=60, t=15, b=40, pad=5),
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Matchday",
            linecolor="black",
            showgrid=False,
            showline=False,
            fixedrange=True,  # Disable zooming/panning
            range=[form_df['matchday'].min(), form_df['matchday'].max()]  # Dynamic x-axis range
        ),
        yaxis=dict(
            title="Points",
            gridcolor="gray",
            showgrid=False,
            showline=False,
            zeroline=False,
            fixedrange=True,  # Disable zooming/panning
            ticktext=y_labels,
            tickvals=y_labels,
            range=[-1, max(form_df['cumPoints']) + 1]  # Dynamic y-axis range
        ),
        dragmode=False,  # Disable drag interactions
        showlegend=False  # Hide legend
    )

    return html.Div([
        html.H1("Points", style={'text-align': 'center'}),
        dcc.Graph(figure=fig,config={'displayModeBar': False,
            'showSendToCloud': False})
    ])

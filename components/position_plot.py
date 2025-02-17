import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
from utils.constants import clean_names, team_colors

def get_position_line(form_df, team, is_main_team):
    """Creates a single team's position line for the plot."""
    # Filter and process data for the team
    team_df = form_df[form_df['team'] == team].copy()
    team_df['date'] = team_df['date'].dt.strftime('%Y %b %d')

    if team_df.empty:
        return None  # Skip if no data

    line_color = team_colors.get(team, {'primary': '#c600d8', 'secondary': '#000'})['primary'] if is_main_team else '#d3d3d3'
    
    # Use customdata so that the team name appears correctly in the hover text
    return go.Scatter(
        x=team_df['matchday'],
        y=team_df['position'],
        mode='lines',
        line=dict(color=line_color, width=4 if is_main_team else 2),
        text=team_df['date'].astype(str),
        customdata=team_df[['team']],
        hovertemplate="<b>%{customdata[0]}</b><br>Matchday %{x}<br>%{text}<br>Position: <b>%{y:.0f}</b><extra></extra>",
        showlegend=False  # Hide legend
    )

def build_position_time_plot(form_df, selected_team):
    """Generates the full position plot with reversed y-axis (rank 1 at the top)
    and colored background bands for different qualification/relegation zones."""
    # Clean/prepare data
    form_df = form_df.copy()
    form_df['team'] = form_df['team']
    # drop na values whre score is null
    form_df = form_df.dropna(subset=['score'])
    form_df['date'] = pd.to_datetime(form_df['date'])
    form_df['matchday'] = form_df['matchday'].astype(int)
    form_df['position'] = form_df['position'].astype(int)
    
    teams = form_df['team'].unique()
    
    # Create one trace per team. The selected team gets a thicker, colored line.
    traces = [get_position_line(form_df, team, team == selected_team) for team in teams if team != selected_team]
    traces.append(get_position_line(form_df, selected_team, True))
    traces = [trace for trace in traces if trace]  # Remove any None values

    # --- Define background shapes ---
    # Note: Because we reversed the y-axis below (so that lower position numbers are at the top),
    # we define shapes using the actual position values.
    # For example, to cover positions 1-4 we cover from y=0.5 to y=4.5.
    shapes = [
        # UEFA Champions League group stage: positions 1-4
        {
            'type': 'rect',
            'xref': 'paper',  # across full horizontal width
            'yref': 'y',
            'x0': 0,
            'x1': 1,
            'y0': 0.5,
            'y1': 4.5,
            'fillcolor': 'rgba(0, 128, 0, 0.3)',  # green tint
            'line': {'width': 0},
            'layer': 'below'
        },
        # Europa League group stage: position 5 only
        {
            'type': 'rect',
            'xref': 'paper',
            'yref': 'y',
            'x0': 0,
            'x1': 1,
            'y0': 4.5,
            'y1': 5.5,
            'fillcolor': 'rgba(0, 0, 255, 0.3)',  # blue tint
            'line': {'width': 0},
            'layer': 'below'
        },
        # Europa Conference League qualifiers: position 6 only
        {
            'type': 'rect',
            'xref': 'paper',
            'yref': 'y',
            'x0': 0,
            'x1': 1,
            'y0': 5.5,
            'y1': 6.5,
            'fillcolor': 'rgba(255, 165, 0, 0.3)',  # orange tint
            'line': {'width': 0},
            'layer': 'below'
        },
        # Relegation: positions 18-20
        {
            'type': 'rect',
            'xref': 'paper',
            'yref': 'y',
            'x0': 0,
            'x1': 1,
            'y0': 17.5,
            'y1': 20.5,
            'fillcolor': 'rgba(255, 0, 0, 0.3)',  # red tint
            'line': {'width': 0},
            'layer': 'below'
        }
    ]
    
    # Create the figure and update layout
    fig = go.Figure(traces)
    fig.update_layout(
        autosize=True,
        margin=dict(r=20, l=60, t=15, b=40, pad=5),
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",  # White plot background
        paper_bgcolor="rgba(0,0,0,0)",  # Light gray paper background
        shapes=shapes,
        xaxis=dict(
            title="Matchday",
            linecolor="black",
            showgrid=False,
            showline=False,
            fixedrange=True,
            range=[form_df['matchday'].min(), form_df['matchday'].max()]  # Dynamic x-axis range
        ),
        yaxis=dict(
            title="Position",
            gridcolor="gray",
            showgrid=False,
            showline=False,
            zeroline=False,
            fixedrange=True,
            tickmode='linear',
            dtick=1,
            range=[len(teams)+0.5, 0.5],  # Reverse the y-axis so position 1 is at the top
            autorange=False  # Using our specified range
        ),
        dragmode=False,
        showlegend=False
    )

    return html.Div([
        html.H1("Position", style={'text-align': 'center'}),
        dcc.Graph(figure=fig,config={'displayModeBar': False,
            'showSendToCloud': False})
    ])
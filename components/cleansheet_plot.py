import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd

def get_played_matchdays(form_df, team: str) -> list:
    """
    Returns a sorted list of matchday keys from the current season.
    Adjust the sorting as needed (here assuming keys can be cast to int).
    """
    team_df = form_df[form_df['team'] == team].copy()
    # drop rows where score is null
    team_df = team_df.dropna(subset=['score'])
    match_days = team_df['matchday'].unique().tolist()
    
    # Return sorted matchday keys (as strings)
    return sorted(match_days, key=lambda x: int(x))

def get_team_clean_sheets(form_df, team: str, matchdays: list) -> list:

    clean_sheets = []
    form_df = form_df[form_df['team'] == team].copy()
    dict_form_df=form_df.to_dict('records')

    for matchday in matchdays:
      for row in dict_form_df:
        if row['matchday'] == matchday:
          score=row['score']
          atHome=row['atHome']
          if pd.isnull(score):
            clean_sheets.append(0)
          else:
            if atHome:
              homeGoals, awayGoals = map(int, score.split('-'))
              clean_sheets.append(1 if awayGoals == 0 else 0)
            else:
              awayGoals, homeGoals = map(int, score.split('-'))
              clean_sheets.append(1 if awayGoals == 0 else 0)
    return clean_sheets


def create_clean_sheets_figure(form_df, team: str) -> html.Div:

    # Compute matchdays (labels). Here we use the played matchdays.
    matchdays = get_played_matchdays(form_df, team)
    
    # Compute clean sheets (a list of 0 or 1 for each matchday)
    clean_sheets = get_team_clean_sheets(form_df, team, matchdays)
    # Create the inverse (if clean sheet is 0, then goals conceded = 1, else 0)
    not_clean_sheets = [1 if cs == 0 else 0 for cs in clean_sheets]
    
    # Create bar traces: one for clean sheets and one for goals conceded.
    trace_clean = go.Bar(
        name='Clean sheets',
        type='bar',
        x=matchdays,
        width=0.3,
        y=clean_sheets,
        marker=dict(color='#00FF00'),
        hovertemplate='<b>Clean sheet</b><extra></extra>',
        showlegend=False
    )
    trace_conceded = go.Bar(
        name='Conceded',
        type='bar',
        width=0.3,
        x=matchdays,
        y=not_clean_sheets,
        marker=dict(color='#F5271D'),
        hovertemplate='<b>Goals conceded</b><extra></extra>',
        showlegend=False
    )
    
    # A hidden line added so that the x-axis spans the proper length.
    hidden_line = go.Scatter(
        name='Hidden',
        mode='lines',
        x=matchdays,
        y=[1.1] * len(matchdays),
        line=dict(color='#FAFAFA', width=1),
        hoverinfo='skip',
        showlegend=False
    )
    

    if matchdays:
        baseline_shape = dict(
            type='line',
            x0=matchdays[0],
            y0=0.5,
            x1=matchdays[-1],
            y1=0.5,
            layer='below',
            line=dict(color='#d3d3d3', width=2)
        )
    else:
        baseline_shape = {}
    # split score value and sum the away and home goals, a nd get the max value
    # drop na values whre score is null
    form_df = form_df.dropna(subset=['score'])
    max_value=form_df['score'].str.split('-').apply(lambda x: sum(map(int, x))).max()
    form_df = form_df.copy()
    form_df= form_df[form_df['team']==team]
    max_matchday = form_df['matchday'].max()
    # Build the layout.
    layout = dict(
        title=False,
        autosize=True,
        height=60,
        margin=dict(r=20, l=60, t=0, b=40, pad=5),
        barmode='stack',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            showticklabels=False,
            gridcolor='gray',
            showgrid=False,
            showline=False,
            zeroline=False,
            fixedrange=True,
        ),
        xaxis=dict(
            title=dict(text='Matchday'),
            linecolor='black',
            showgrid=False,
            showline=False,
            fixedrange=True,
            tickmode='array',
            tickvals=matchdays,
            range=[0.5, max_matchday + 0.5]  # Dynamic x-axis
        ),
        shapes=[baseline_shape],
        dragmode=False,
        showlegend=False
    )
    
    # Build the full figure.
    fig = go.Figure(data=[trace_clean, trace_conceded, hidden_line], layout=layout)
    return fig

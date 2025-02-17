import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
from collections import defaultdict
from utils.constants import clean_names
from components.cleansheet_plot import  create_clean_sheets_figure
def get_avg_goals_per_game(form_df):
    avg_goals = defaultdict(int)
    teams = form_df['team'].unique().tolist()
    num_teams = len(teams)

    dict_data=form_df.to_dict('records')
    for match in dict_data:
        score = match['score']
        if pd.isnull(score):
            continue
        home_goals, away_goals = map(int, score.split('-'))
        matchday = match['matchday']
        avg_goals[matchday] += home_goals + away_goals

    # Divide by the number of teams to get average goals per matchday
    avg_goals = {md: goals / num_teams for md, goals in avg_goals.items()}
    
    return avg_goals

def get_team_goals_per_game(form_df, team):
    scored, conceded = {}, {}
    form_df_team = form_df[form_df['team'] == team]

    dict_data=form_df_team.to_dict('records')
    for match in dict_data:
        score = match['score']
        if pd.isnull(score):
            continue

        if match['atHome']:
            home_goals, away_goals = map(int, score.split('-'))
            scored[match['matchday']] = home_goals
            conceded[match['matchday']] = away_goals
        else:
            away_goals, home_goals = map(int, score.split('-'))
            scored[match['matchday']] = away_goals
            conceded[match['matchday']] = home_goals
    
    return scored, conceded

def avg_line( avg_goals, matchdays):
    return go.Scatter(
        name='Avg',
        x=matchdays ,
        y=[avg_goals[md] for md in matchdays],
        text=matchdays,
        mode='lines',
        line=dict(color='#0080FF', width=2),
        hovertemplate='<b>Matchday %{text}</b><br>%{y:.1f} goals<extra></extra>'
    )

def team_scored_bar( team_scored, matchdays,opponent: list):
    # add opponent to the hovertemplate Machday x goals scored/nOpponent
    return go.Bar(
        name='Scored',
        x=matchdays,
        width=0.3,
        y=[team_scored.get(md,0) for md in matchdays],
        customdata=opponent,
        marker=dict(color='#00FF00'),
        # hovertemplate='<b>Matchday %{x}</b><br>%{y} goals scored<extra></extra>'
        hovertemplate='<b>Matchday %{x}</b><br>%{y} goals scored<br>Opponent: %{customdata}<extra></extra>'
    )

def team_conceded_bar( team_conceded, matchdays,opponent: list):

    return go.Bar(
        name='Conceded',
        x=matchdays,
        width=0.3,
        y=[team_conceded.get(md,0) for md in matchdays],
        marker=dict(color='#F5271D'),
        # hovertemplate='<b>Matchday %{x}</b><br>%{y} goals conceded<extra></extra>'
        customdata=opponent,
        hovertemplate='<b>Matchday %{x}</b><br>%{y} goals conceded<br>Opponent: %{customdata}<extra></extra>'
    )

def default_layout(form_df,team):
    # split score value and sum the away and home goals, a nd get the max value
    # drop na values whre score is null
    form_df = form_df.dropna(subset=['score'])
    max_value=form_df['score'].str.split('-').apply(lambda x: sum(map(int, x))).max()
    form_df = form_df.copy()
    form_df= form_df[form_df['team']==team]
    max_matchday = form_df['matchday'].max()
    
    return dict(
        autosize=True,
        margin=dict(r=20, l=60, t=15, b=15, pad=5),
        barmode='stack',
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title=dict(text='Goals'),
            gridcolor='gray',
            showgrid=False,
            showline=False,
            zeroline=False,
            fixedrange=True,
            range=[0,max_value],
            visible=True,
            tickformat='d'
        ),
        xaxis=dict(
            linecolor='black',
            showgrid=False,
            showline=False,
            fixedrange=True,
            showticklabels=False,
            range=[0.5, max_matchday+0.5]  # Dynamic x-axis
        ),
        legend=dict(
            x=1,
            xanchor='right',
            y=1
        ),
        dragmode=False
    )

def build_goals_per_game_barchart(form_df, team):

    team_scored, team_conceded = get_team_goals_per_game(form_df, team)
    avg_goals = get_avg_goals_per_game(form_df)
    matchdays = list(avg_goals.keys())

    temp_Df = form_df.dropna(subset=['score'])
    temp_Df = temp_Df[temp_Df['team'] == team]
    # apply clean_names to the opponent column
    temp_Df['opponent'] = temp_Df['opponent'].apply(lambda x: clean_names.get(x, x))
    opponent = temp_Df['opponent'].tolist()
    


    scored_bar = team_scored_bar( team_scored, matchdays,opponent)
    conceded_bar = team_conceded_bar( team_conceded, matchdays,opponent)
    line = avg_line( avg_goals, matchdays)

    data= [scored_bar, conceded_bar, line]

    fig = go.Figure(data=data, layout=default_layout(form_df,team))

    clean_fig=create_clean_sheets_figure(form_df, team)

    return html.Div([
        html.H1("Goals Per Game", style={'text-align': 'center'}),
        dcc.Graph(figure=fig, config={
            'displayModeBar': False,
            'showSendToCloud': False
        }),
        dcc.Graph(figure=clean_fig, config={
            'displayModeBar': False,
            'showSendToCloud': False
        })
    ])


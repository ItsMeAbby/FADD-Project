import plotly.graph_objs as go
import pandas as pd
from utils.constants import clean_names

def build_fixture_plot_data(fixtures_df, team_ratings_df, home_advantages_df, team):
    now = pd.Timestamp.now()
    line = get_line(fixtures_df, team_ratings_df, home_advantages_df, team, now)
    dates = line.x
    layout = default_layout(dates, now)
    fig = go.Figure(data=[line], layout=layout)
    return fig

def get_line(fixtures_df, team_ratings_df, home_advantages_df, team, now):
    fixtures = fixtures_df[fixtures_df['team'] == team].sort_values('date')
    x, y, descriptions = line_points(fixtures, team_ratings_df, home_advantages_df, team)
    sizes = [13] * len(x)
    sizes = highlight_next_game_marker(sizes, x, now, 26)

    return go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',
        text=descriptions,
        line=dict(color='#737373'),
        marker=dict(
            size=sizes,
            colorscale=[[0, '#00fe87'], [0.5, '#f3f3f3'], [1, '#f83027']],
            color=y,
            opacity=1,
            line=dict(width=1)
        ),
        hovertemplate='<b>%{text}</b><br>%{x|%d %b %Y}<br>Opponent Rating: <b>%{y:.1f}%</b><extra></extra>'
    )

def line_points(fixtures, team_ratings_df, home_advantages_df, team):
    x = []
    y = []
    descriptions = []
    for _, match in fixtures.iterrows():
        date = pd.to_datetime(match['date'])
        x.append(date)
        opposition_rating = get_opposition_team_rating(team_ratings_df, home_advantages_df, match['opponent'], match['atHome'])
        y.append(opposition_rating * 100)
        descriptions.append(match_description(team, match))
    return x, y, descriptions

def get_opposition_team_rating(team_ratings_df, home_advantages_df, opponent_team, at_home):
    rating_row = team_ratings_df[team_ratings_df['team'] == opponent_team]
    if not rating_row.empty:
        opposition_rating = rating_row.iloc[0]['total']
    else:
        opposition_rating = 0

    if at_home:
        home_adv_row = home_advantages_df[home_advantages_df['team'] == opponent_team]
        if not home_adv_row.empty:
            total_home_advantage = home_adv_row.iloc[0]['totalHomeAdvantage']
            opposition_rating *= (1 - total_home_advantage)
    return opposition_rating

def match_description(team, match):
    home_team = match["team"] if match['atHome'] else match['opponent']
    away_team = match['opponent'] if match['atHome'] else match['team']
    home_team = clean_names.get(home_team, home_team)
    away_team = clean_names.get(away_team, away_team)
    if pd.notnull(match['homeScore']) and pd.notnull(match['awayScore']):
        scoreline = f"{int(match['homeScore'])}-{int(match['awayScore'])}"
        return f"{home_team} {scoreline} {away_team}"
    else:
        return f"{home_team} vs {away_team}"

def current_date_line(now, max_x):
    if now > max_x:
        return None
    return dict(
        type='line',
        x0=now,
        y0=-4,
        x1=now,
        y1=104,
        line=dict(color='black', dash='dot', width=1)
    )

def x_range(dates):
    min_x = dates[0] - pd.Timedelta(days=7)
    max_x = dates[-1] + pd.Timedelta(days=7)
    return min_x, max_x

def default_layout(x, now):
    y_labels = [i * 10 for i in range(11)]
    min_x, max_x = x_range(x)
    current_date_shape = current_date_line(now, max_x)
    layout = go.Layout(
        autosize=True,
        margin=dict(r=20, l=60, t=5, b=40, pad=5),
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            title='Opponent Rating',
            gridcolor='#d6d6d6',
            showline=False,
            zeroline=False,
            fixedrange=True,
            tickvals=y_labels,
            ticktext=y_labels
        ),
        xaxis=dict(
            showgrid=False,
            showline=False,
            range=[min_x, max_x],
            fixedrange=True
        ),
        shapes=[current_date_shape] if current_date_shape else [],
        dragmode=False
    )
    return layout

def highlight_next_game_marker(sizes, dates, now, highlight_size):
    next_game_idx = None
    min_diff = float('inf')
    for i, date in enumerate(dates):
        diff = (date - now).total_seconds()
        if 0 < diff < min_diff:
            min_diff = diff
            next_game_idx = i
    if next_game_idx is not None:
        sizes[next_game_idx] = highlight_size
    return sizes
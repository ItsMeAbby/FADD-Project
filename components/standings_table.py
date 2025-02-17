from dash import html
from utils.constants import team_colors, clean_names

def build_table_snippet(standings_df, team):
    snippet_df, team_table_idx = get_table_snippet_range(standings_df, team)
    team_color = team_colors.get(team, {'primary': '#000000', 'secondary': '#ffffff'})
    
    # Base styles
    base_cell_style = {
        "padding": "2px 2px",  # Consistent padding for all cells
        "whiteSpace": "nowrap",
        "overflow": "hidden",
        "textOverflow": "ellipsis"
    }
    
    rows = []
    for idx, row in snippet_df.iterrows():
        is_current_team = row['team'] == team

        # Row style
        row_style = {
            "transition": "all 0.2s ease-in-out",
            "borderRadius": "4px",
            "margin": "2px 0",
        }
        
        if is_current_team:
            row_style.update({
                "backgroundColor": team_color['primary'],
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "transform": "scale(1.01)",
            })

        # Cell styles with proper alignment
        cell_styles = {
            "position": {
                **base_cell_style,
                "width": "10%",
                "textAlign": "center",
                "fontWeight": "500",
            },
            "team": {
                **base_cell_style,
                "width": "54%",
                "textAlign": "left",
                "fontWeight": "500",
            },
            "gd": {
                **base_cell_style,
                "width": "12%",
                "textAlign": "center",
            },
            "points": {
                **base_cell_style,
                "width": "12%",
                "textAlign": "center",
                "fontWeight": "600",
            }
        }

        # Apply highlight colors to text
        if is_current_team:
            for style in cell_styles.values():
                style["color"] = team_color['secondary']

        # Create cells with proper styling
        row_cells = [
            html.Td(
                row['position'],
                style=cell_styles["position"]
            ),
            html.Td(
                clean_names.get(row['team'], row["team"]),
                style=cell_styles["team"]
            ),
            html.Td(
                row['playedGames'],
                style=cell_styles["gd"]
            ),
            html.Td(
                row['goalDifference'],
                style=cell_styles["gd"]
            ),
            html.Td(
                row['points'],
                style=cell_styles["points"]
            )
        ]

        rows.append(html.Tr(row_cells, style=row_style))
    
    # Header styles
    header_cell_style = {
        **base_cell_style,
        "fontWeight": "600",
        "borderBottom": "2px solid #eee",
        "backgroundColor": "#f8f9fa",
    }
    
    table_header = html.Thead(html.Tr([
        html.Th('', style={**header_cell_style, "width": "10%", "textAlign": "center"}),
        html.Th('Team', style={**header_cell_style, "width": "54%", "textAlign": "left"}),
        html.Th('MP', style={**header_cell_style, "width": "12%", "textAlign": "center"}),
        html.Th('GD', style={**header_cell_style, "width": "12%", "textAlign": "center"}),
        html.Th('Points', style={**header_cell_style, "width": "12%", "textAlign": "center"})
    ]))
    
    return html.Table(
        [table_header, html.Tbody(rows)],
        style={
            'width': '100%',
            'borderCollapse': 'separate',
            'borderSpacing': '0 4px',
            'backgroundColor': '#ffffff',
            'borderRadius': '8px',
            'padding': '16px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.1)',
        }
    )

# Keep the get_table_snippet_range function unchanged
def get_table_snippet_range(standings_df, team):
    df_sorted = standings_df.sort_values('position').reset_index(drop=True)
    team_idx = df_sorted[df_sorted['team'] == team].index[0]
    if team_idx < 3:
        snippet_df = df_sorted.iloc[:7]
        team_table_idx = team_idx
    elif team_idx > len(df_sorted) - 4:
        snippet_df = df_sorted.iloc[-7:]
        team_table_idx = 6 - (len(df_sorted) - 1 - team_idx)
    else:
        snippet_df = df_sorted.iloc[team_idx - 3:team_idx + 4]
        team_table_idx = 3
    return snippet_df, team_table_idx
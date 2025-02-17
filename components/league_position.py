
from dash import html
def get_position(position, team_color):
  return html.Div([
        # Position number
        html.Div(str(position), 
                 style={
                    'fontSize': '20vw',
                    'color': '#333',
                    'position': 'absolute',
                    'transform': 'translate(-50%, -50%)',
                    'left': '50%',
                    'top': '50%',
                    'zIndex': '2',
                    'fontWeight': '800',
                    'textShadow': '9px 9px #000',
                    'userSelect': 'none',
                    "zIndex": "20"
                }
        ),
        # Large circle (bottom)
        html.Div(style={
            'backgroundColor': team_color['primary'],
            'borderRadius': '50%',
            'width': '280px',
            'height': '280px',
            'position': 'absolute',
            'transform': 'translate(-50%, -50%)',
            'left': '60%',
            'top': '64%',
            'zIndex': '10'
        }),
        # Medium circle (middle)
        html.Div(style={
            'backgroundColor': team_color['primary'],
            'borderRadius': '50%',
            'width': '220px',
            'height': '220px',
            'position': 'absolute',
            'transform': 'translate(-50%, -50%)',
            'left': '34%',
            'top': '34%',
            'zIndex': '10'
        }),
        # Small circle (top)
        html.Div(style={
            'backgroundColor': team_color['secondary'],
            'borderRadius': '50%',
            'width': '150px',
            'height': '150px',
            'position': 'absolute',
            'transform': 'translate(-50%, -50%)',
            'left': '60%',
            'top': '30%',
            'zIndex': '0'
        }),
    ], style={
        'position': 'relative',
        'maxWidth': '400px',
        'maxHeight': '400px',
        'width': '400px',
        'height': '400px',
        'margin': '0 auto'
    })
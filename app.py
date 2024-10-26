import os
from dash import Dash, html, dcc, Input, Output, State
from flask import send_from_directory

app = Dash(__name__)
server = app.server  # Expose the Flask server for deployment

# Favicon route
@server.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(server.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )

# Dash Layout
app.layout = html.Div([
    html.H1("Welcome to the Index Page"),
    html.Div(id='output-message'),
    dcc.Input(id='name-input', type='text', placeholder='Enter your name'),
    html.Button('Submit', id='submit-button', n_clicks=0),
])

# Callback for greeting message
@app.callback(
    Output('output-message', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('name-input', 'value')]
)
def greet_user(n_clicks, name):
    if n_clicks > 0:
        if name:
            return f"Hello, {name}!"
        else:
            return "No name entered; please enter a name."
    return ""

if __name__ == '__main__':
    app.run_server(debug=True)

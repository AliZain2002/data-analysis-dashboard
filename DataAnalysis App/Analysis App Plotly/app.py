import dash
import flask
import dash_bootstrap_components as dbc

# Initialize Flask server
server = flask.Flask(__name__)

# Initialize Dash application
app = dash.Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
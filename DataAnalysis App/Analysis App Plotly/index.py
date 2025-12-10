import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import io

from app import app
from pages import home, preprocessing, univariate, bivariate

# --- Navigation Bar Layout ---
NAV_BAR = html.Nav(
    className='navbar navbar-expand-lg navbar-light bg-light',
    children=[
        html.Div(
            className='container-fluid',
            children=[
                html.A(
                    className='navbar-brand',
                    children='Data Analysis App',
                    href='/',
                    style={'fontWeight': 'bold', 'fontSize': '1.5em'}
                ),
                html.Ul(
                    className='navbar-nav',
                    children=[
                        html.Li(className='nav-item', children=dcc.Link('Home', href='/', className='nav-link')),
                        html.Li(className='nav-item', children=dcc.Link('Preprocessing', href='/preprocessing', className='nav-link')),
                        html.Li(className='nav-item', children=dcc.Link('Univariate Analysis', href='/univariate', className='nav-link')),
                        html.Li(className='nav-item', children=dcc.Link('Bivariate Analysis', href='/bivariate', className='nav-link')),
                    ]
                )
            ]
        )
    ]
)

# --- Global Data Store (dcc.Store) ---
# A dcc.Store component is used to share data (the uploaded DataFrame) across pages.
# It stores data in the browser's memory.
GLOBAL_STORE = dcc.Store(id='stored-data', storage_type='session')

app.layout = html.Div([
    dcc.Location(id='url', refresh=False), # Component to track the URL
    GLOBAL_STORE,                         # Component to store the uploaded data
    NAV_BAR,                              # Navigation bar
    html.Div(id='page-content', className='container mt-4') # Content container
])

# --- Main Callback for Page Routing ---
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """Routes the URL to the appropriate page layout."""
    if pathname == '/preprocessing':
        return preprocessing.layout
    elif pathname == '/univariate':
        return univariate.layout
    elif pathname == '/bivariate':
        return bivariate.layout
    elif pathname == '/':
        return home.layout
    else:
        return html.Div([html.H1('404'), html.P('Page not found')])

# --- Data Upload and Storage Callback (Defined in index.py to share data) ---
# This callback parses the uploaded file content and stores the resulting DataFrame (as JSON string)
# in the dcc.Store component.
@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def store_data(contents, filename):
    """
    Parses the uploaded CSV file and stores the data as a JSON string in the global store.
    """
    if contents is None:
        return None

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        # Assume CSV file uploaded
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        # Convert DataFrame to JSON (optimized for storage)
        return df.to_json(date_format='iso', orient='split')
    except Exception as e:
        print(f"Error processing file: {e}")
        return None # Return None if parsing fails

# --- Run the App ---
if __name__ == '__main__':
    # You may need to change the port if it's in use
    app.run(debug=True, port=8050)
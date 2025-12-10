from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io

# --- Layout ---
layout = html.Div(
    style={'textAlign': 'center', 'padding': '50px'},
    children=[
        html.H1("📊 Data Analysis Dashboard", className="display-4"),
        html.P("Upload your CSV file to begin. The data will be available across all tabs.", className="lead"),
        html.Hr(className="my-4"),

        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select a CSV File', style={'fontWeight': 'bold', 'textDecoration': 'underline'})
            ]),
            style={
                'width': '60%',
                'height': '100px',
                'lineHeight': '100px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'textAlign': 'center',
                'margin': '0 auto',
                'backgroundColor': '#f8f9fa',
                'cursor': 'pointer'
            },
            multiple=False
        ),
        
        # This Div will show the Success Message or Error
        html.Div(id='upload-success-message', className='mt-4')
    ]
)

# --- Callback for Success Message ---
# This runs separately from the index.py storage callback just to update the UI
@callback(
    Output('upload-success-message', 'children'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return html.Div("Waiting for file...", style={'color': 'gray', 'fontStyle': 'italic'})

    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the file just to get stats (Row/Col count)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        # --- THE FIX IS HERE ---
        # We use f-strings (f"...") to automatically handle numbers and text together.
        rows = df.shape[0]
        cols = df.shape[1]

        return html.Div([
            html.H4("✅ File Uploaded Successfully!", className="text-success"),
            html.P(f"Filename: {filename}"),
            html.P(f"Dataset contains {rows} rows and {cols} columns."),
            dbc.Button("Go to Preprocessing", href="/preprocessing", color="primary", className="mt-2")
        ], className="alert alert-success", style={'maxWidth': '600px', 'margin': '20px auto'})

    except Exception as e:
        return html.Div([
            html.H5("❌ Error processing file"),
            html.P(str(e))
        ], className="alert alert-danger")
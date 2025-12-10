from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from app import app

# --- Layout ---
layout = html.Div([
    html.H2("📊 Univariate Analysis (Histograms)"),
    html.P("Analyze the distribution of a single variable. Use settings to refine the plot."),
    
    html.Div(className='card p-3 shadow-sm', children=[
        html.Div(className='row', children=[
            # Column 1: Main Controls
            html.Div(className='col-md-6', children=[
                html.Label("Select Column to Analyze (X-Axis):", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='uni-x-col', placeholder='Choose a column...'),
                
                html.Br(),
                html.Label("Group By (Color) - Optional:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='uni-color-col', placeholder='Choose a categorical column...')
            ]),

            # Column 2: Histogram Settings
            html.Div(className='col-md-6', children=[
                html.Label("Number of Bins (for numbers):", style={'fontWeight': 'bold'}),
                dcc.Slider(
                    id='uni-nbins',
                    min=5, max=100, step=5, value=20,
                    marks={10: '10', 50: '50', 100: '100'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                
                html.Br(),
                html.Label("Visualization Options:", style={'fontWeight': 'bold'}),
                dcc.Checklist(
                    id='uni-options',
                    options=[
                        {'label': ' Show Box Plot (Outliers)', 'value': 'box'},
                        {'label': ' Log Scale (Fix Skewed Data)', 'value': 'log'}
                    ],
                    value=['box'], # Default checked
                    inline=True
                )
            ])
        ])
    ]),

    html.Br(),
    
    # Graph Container
    dcc.Loading(
        id="loading-1",
        type="default",
        children=dcc.Graph(id='uni-graph', style={'height': '600px'})
    )
])

# --- Callbacks ---

# 1. Populate Dropdowns
@app.callback(
    [Output('uni-x-col', 'options'),
     Output('uni-color-col', 'options')],
    [Input('stored-data', 'data')]
)
def populate_dropdowns(json_data):
    if json_data is None: return [], []
    
    try:
        # Load data just to get column names
        df = pd.read_json(json_data, orient='split')
        options = [{'label': col, 'value': col} for col in df.columns]
        return options, options
    except:
        return [], []

# 2. Generate Histogram
@app.callback(
    Output('uni-graph', 'figure'),
    [Input('uni-x-col', 'value'),
     Input('uni-color-col', 'value'),
     Input('uni-nbins', 'value'),
     Input('uni-options', 'value'),
     Input('stored-data', 'data')]
)
def update_histogram(x_col, color_col, nbins, options, json_data):
    if json_data is None or x_col is None:
        return {}

    try:
        df = pd.read_json(json_data, orient='split')
        
        # Check settings
        show_box = "box" if "box" in options else None
        use_log = True if "log" in options else False

        # Create Plot
        fig = px.histogram(
            df,
            x=x_col,
            color=color_col,
            nbins=nbins,
            marginal=show_box, # Adds the box plot on top
            log_y=use_log,     # Helpful for income/loan amounts
            title=f"Distribution of {x_col}",
            template="plotly_white",
            barmode="overlay", # Good for comparing groups
            opacity=0.7
        )

        fig.update_layout(
            bargap=0.1, 
            xaxis_title=x_col, 
            yaxis_title="Count"
        )
        
        return fig

    except Exception as e:
        print(f"Error: {e}")
        return {}
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

from app import app # Import the app instance

layout = html.Div([
    html.H2('📉 Bivariate Analysis', className='mb-4'),
    html.P('Examine relationships between two variables.'),
    
    html.Div([
        html.Div([
            # --- Column Selection Dropdowns ---
            html.Div([
                html.Label('Select X-Axis Column:'),
                dcc.Dropdown(id='bivariate-x-select', placeholder='Select X-axis column', className='mb-3'),
            ], style={'flex': '1', 'marginRight': '10px'}),
            
            html.Div([
                html.Label('Select Y-Axis Column:'),
                dcc.Dropdown(id='bivariate-y-select', placeholder='Select Y-axis column', className='mb-3'),
            ], style={'flex': '1', 'marginLeft': '10px'}),
        ], style={'display': 'flex', 'marginBottom': '20px'}),
        
        # --- Plot Type Selector ---
        html.Div([
            html.Label('Select Plot Type:'),
            dcc.RadioItems(
                id='bivariate-plot-type',
                options=[
                    {'label': 'Scatter Plot', 'value': 'scatter'},
                    {'label': 'Line Plot', 'value': 'line'}
                ],
                value='scatter',  # Default selection
                inline=True,
                style={'padding': '10px 0'}
            ),
        ]),
        
        # Div to hold the generated Plotly graph
        dcc.Graph(id='bivariate-graph')
        
    ], className='card p-3 shadow-sm')
])

# --- Callback 1: Populate Dropdown Options ---
@app.callback(
    Output('bivariate-x-select', 'options'),
    Output('bivariate-y-select', 'options'),
    [Input('stored-data', 'data')]
)
def set_column_options(json_data):
    """Retrieves data and populates both X and Y dropdowns with column names."""
    if json_data is None:
        return [], []
    
    try:
        df = pd.read_json(json_data, orient='split')
        options = [{'label': col, 'value': col} for col in df.columns]
        return options, options
    except Exception:
        return [], []

# --- Callback 2: Generate Bivariate Plot ---
@app.callback(
    Output('bivariate-graph', 'figure'),
    [
        Input('bivariate-x-select', 'value'),
        Input('bivariate-y-select', 'value'),
        Input('bivariate-plot-type', 'value'),
        Input('stored-data', 'data')
    ]
)
def generate_bivariate_plot(x_col, y_col, plot_type, json_data):
    """Generates a scatter or line plot based on user selection."""
    
    # Check if data or necessary columns are selected
    if json_data is None or x_col is None or y_col is None:
        return {}

    try:
        df = pd.read_json(json_data, orient='split')
        
        if plot_type == 'scatter':
            fig = px.scatter(
                df, 
                x=x_col, 
                y=y_col, 
                title=f'Scatter Plot: {x_col} vs {y_col}',
                height=550
            )
        elif plot_type == 'line':
            # Note: Plotly Express's line plot can be used for general data, 
            # though it's typically best for data ordered by an index or time.
            fig = px.line(
                df.sort_values(by=x_col), # Sort by X for a cleaner line path
                x=x_col, 
                y=y_col, 
                title=f'Line Plot: {x_col} vs {y_col}',
                height=550
            )
        else:
            return {}

        fig.update_layout(transition_duration=500)
        return fig
        
    except Exception as e:
        print(f"Error generating bivariate plot: {e}")
        return {}
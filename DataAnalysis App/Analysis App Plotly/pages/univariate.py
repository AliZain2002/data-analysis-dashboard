from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from app import app

# --- Layout ---
layout = html.Div([
    html.H2("📈 Univariate Analysis"),
    html.P("Analyze the distribution of a single variable using different plot types."),
    
    html.Div(className='card p-3 shadow-sm', children=[
        html.Div(className='row', children=[
            # Column 1: Main Controls
            html.Div(className='col-md-4', children=[
                html.Label("1. Select Column (X-Axis):", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='uni-x-col', placeholder='Choose a column...'),
                
                html.Br(),
                html.Label("2. Group By (Color) - Optional:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='uni-color-col', placeholder='Split by category...')
            ]),

            # Column 2: Plot Type Selector
            html.Div(className='col-md-4', children=[
                html.Label("3. Select Plot Type:", style={'fontWeight': 'bold'}),
                dcc.RadioItems(
                    id='uni-plot-type',
                    options=[
                        {'label': ' 📊 Histogram', 'value': 'hist'},
                        {'label': ' 📦 Box Plot', 'value': 'box'},
                        {'label': ' 🎻 Violin Plot', 'value': 'violin'}
                    ],
                    value='hist',
                    labelStyle={'display': 'block', 'marginBottom': '10px'}
                )
            ]),

            # Column 3: Settings (Dynamic)
            html.Div(className='col-md-4', children=[
                html.Label("4. Settings:", style={'fontWeight': 'bold'}),
                
                # Container for Histogram specific settings (Hidden for Box/Violin)
                html.Div(id='hist-settings-container', children=[
                    html.Label("Number of Bins:", style={'fontSize': '0.9em'}),
                    dcc.Slider(
                        id='uni-nbins',
                        min=5, max=100, step=5, value=20,
                        marks={10: '10', 50: '50', 100: '100'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    ),
                ]),

                html.Br(),
                dcc.Checklist(
                    id='uni-options',
                    options=[
                        {'label': ' Log Scale (Fix Skew)', 'value': 'log'},
                        {'label': ' Show Data Points', 'value': 'points'} # For Box/Violin
                    ],
                    value=[], 
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
        df = pd.read_json(json_data, orient='split')
        options = [{'label': col, 'value': col} for col in df.columns]
        return options, options
    except:
        return [], []

# 2. Show/Hide Histogram Settings based on Plot Type
@app.callback(
    Output('hist-settings-container', 'style'),
    [Input('uni-plot-type', 'value')]
)
def toggle_settings(plot_type):
    if plot_type == 'hist':
        return {'display': 'block'}
    else:
        return {'display': 'none'}

# 3. Generate Graph
@app.callback(
    Output('uni-graph', 'figure'),
    [Input('uni-plot-type', 'value'),
     Input('uni-x-col', 'value'),
     Input('uni-color-col', 'value'),
     Input('uni-nbins', 'value'),
     Input('uni-options', 'value'),
     Input('stored-data', 'data')]
)
def update_graph(plot_type, x_col, color_col, nbins, options, json_data):
    if json_data is None or x_col is None:
        return {}

    try:
        df = pd.read_json(json_data, orient='split')
        
        # Check settings
        use_log = True if "log" in options else False
        show_points = "all" if "points" in options else False # "all" shows points, False hides them

        fig = {}

        # --- LOGIC FOR PLOT TYPES ---
        
        if plot_type == 'hist':
            # Histogram
            fig = px.histogram(
                df, x=x_col, color=color_col, nbins=nbins,
                marginal="box", # Always show marginal box for hist
                log_y=use_log,
                title=f"Histogram of {x_col}",
                template="plotly_white", barmode="overlay", opacity=0.7
            )
            fig.update_layout(bargap=0.1, yaxis_title="Count")

        elif plot_type == 'box':
            # Box Plot
            fig = px.box(
                df, x=x_col, color=color_col,
                points=show_points, # Show individual points if selected
                log_x=use_log,      # Log scale on X for box plots
                title=f"Box Plot of {x_col}",
                template="plotly_white"
            )

        elif plot_type == 'violin':
            # Violin Plot
            fig = px.violin(
                df, x=x_col, color=color_col,
                box=True,           # Draw a mini box plot inside the violin
                points=show_points, # Show individual points if selected
                log_x=use_log,
                title=f"Violin Plot of {x_col}",
                template="plotly_white"
            )

        return fig

    except Exception as e:
        print(f"Error: {e}")
        return {}
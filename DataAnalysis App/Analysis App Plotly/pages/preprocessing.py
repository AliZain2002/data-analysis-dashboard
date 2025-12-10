from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import dash
import io
from app import app

# --- Helper Function ---
def parse_data(json_data):
    if json_data is None: return None
    try:
        # Wrap string in io.StringIO to fix FutureWarning
        return pd.read_json(io.StringIO(json_data), orient='split')
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None

# --- Layout ---
layout = html.Div([
    
    # Header & Download Section
    html.Div([
        html.H2("🛠️ Data Preprocessing", style={'display': 'inline-block', 'marginRight': '20px'}),
        
        # Download Component (Invisible helper)
        dcc.Download(id="download-dataframe-csv"),
        
        # Download Button
        html.Button("📥 Download Cleaned CSV", id="btn-download", className="btn btn-success", 
                    style={'verticalAlign': 'top'})
    ], style={'marginBottom': '10px'}),

    html.P("Clean and prepare your dataset. Changes are saved automatically."),
    html.Hr(),

    # Alert Box
    html.Div(id='preprocessing-alert'),

    # Tabs
    dcc.Tabs(id="preprocessing-tabs", value='tab-info', children=[
        dcc.Tab(label='Dataset Info', value='tab-info'),
        dcc.Tab(label='Missing Values', value='tab-missing'),
        dcc.Tab(label='Data Types', value='tab-types'),
        dcc.Tab(label='Column Management', value='tab-columns'),
    ]),

    # --- TAB CONTENT AREAS ---
    
    # 1. Info Tab
    html.Div(id='content-info', style={'display': 'none'}, children=[
        html.Div(id='data-summary-table') 
    ]),

    # 2. Missing Values Tab
    html.Div(id='content-missing', style={'display': 'none'}, children=[
        html.H5("Handle Missing Data"),
        html.Label("Select Column:"),
        dcc.Dropdown(id='missing-col-dropdown', placeholder="Select column..."),
        html.Br(),
        dcc.RadioItems(
            id='missing-action-radio',
            options=[
                {'label': 'Drop Rows with Missing Values', 'value': 'drop_rows'},
                {'label': 'Fill with Mean (Numeric)', 'value': 'mean'},
                {'label': 'Fill with Median (Numeric)', 'value': 'median'},
                {'label': 'Fill with Mode (Frequent)', 'value': 'mode'}
            ],
            value='drop_rows'
        ),
        html.Br(),
        html.Button("Apply Treatment", id='btn-apply-missing', className="btn btn-primary")
    ]),

    # 3. Data Types Tab
    html.Div(id='content-types', style={'display': 'none'}, children=[
        html.H5("Change Data Types"),
        html.P("Convert text columns to numbers (non-numeric values will become NaN).", className="text-muted"),
        html.Label("Select Column:"),
        dcc.Dropdown(id='type-col-dropdown', placeholder="Select column..."),
        html.Br(),
        html.Label("New Type:"),
        dcc.Dropdown(id='type-target-dropdown', 
                     options=[
                         {'label': 'Numeric (Float/Int)', 'value': 'numeric'}, 
                         {'label': 'String (Text)', 'value': 'string'}, 
                         {'label': 'Datetime', 'value': 'datetime'}
                     ], 
                     placeholder="New Type..."),
        html.Br(),
        html.Button("Convert Type", id='btn-apply-type', className="btn btn-warning")
    ]),

    # 4. Column Management Tab
    html.Div(id='content-columns', style={'display': 'none'}, children=[
        html.H5("Drop Columns"),
        dcc.Dropdown(id='drop-col-dropdown', multi=True, placeholder="Select columns..."),
        html.Br(),
        html.Button("Drop Columns", id='btn-apply-drop', className="btn btn-danger")
    ])
])

# --- Callback 1: Control Tab Visibility ---
@app.callback(
    [Output('content-info', 'style'),
     Output('content-missing', 'style'),
     Output('content-types', 'style'),
     Output('content-columns', 'style')],
    [Input('preprocessing-tabs', 'value')]
)
def tab_visibility(tab):
    hide = {'display': 'none'}
    show = {'display': 'block', 'padding': '20px', 'border': '1px solid #ddd', 'borderTop': 'none'}
    if tab == 'tab-info': return show, hide, hide, hide
    if tab == 'tab-missing': return hide, show, hide, hide
    if tab == 'tab-types': return hide, hide, show, hide
    if tab == 'tab-columns': return hide, hide, hide, show
    return show, hide, hide, hide

# --- Callback 2: Populate Options ---
@app.callback(
    [Output('data-summary-table', 'children'),
     Output('missing-col-dropdown', 'options'),
     Output('type-col-dropdown', 'options'),
     Output('drop-col-dropdown', 'options')],
    [Input('stored-data', 'data')]
)
def populate_options(json_data):
    if json_data is None:
        return html.Div("Please upload a dataset on the Home page."), [], [], []
    
    df = parse_data(json_data)
    if df is None: return html.Div("Error loading data"), [], [], []
    
    # Info Table
    summary = pd.DataFrame({
        'Column': df.columns,
        'Type': df.dtypes.astype(str),
        'Nulls': df.isnull().sum()
    })
    
    # Safe F-string formatting
    info_content = html.Div([
        html.H5(f"Dataset Shape: {df.shape[0]} Rows, {df.shape[1]} Columns"),
        dash_table.DataTable(
            data=summary.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in summary.columns],
            page_size=10,
            style_table={'overflowX': 'auto'}
        )
    ])

    col_options = [{'label': col, 'value': col} for col in df.columns]
    type_options = [{'label': f"{col} ({dtype})", 'value': col} for col, dtype in zip(df.columns, df.dtypes)]
    missing_options = [{'label': f"{col} ({df[col].isnull().sum()} missing)", 'value': col} for col in df.columns[df.isnull().any()]]

    return info_content, missing_options, type_options, col_options

# --- Callback 3: Process Data (Apply Buttons) ---
@app.callback(
    [Output('stored-data', 'data', allow_duplicate=True),
     Output('preprocessing-alert', 'children')],
    [Input('btn-apply-missing', 'n_clicks'),
     Input('btn-apply-type', 'n_clicks'),
     Input('btn-apply-drop', 'n_clicks')],
    [State('stored-data', 'data'),
     State('missing-col-dropdown', 'value'),
     State('missing-action-radio', 'value'),
     State('type-col-dropdown', 'value'),
     State('type-target-dropdown', 'value'),
     State('drop-col-dropdown', 'value')],
    prevent_initial_call=True
)
def update_data(btn_miss, btn_type, btn_drop, json_data, 
                miss_col, miss_action, 
                type_col, type_target, 
                drop_cols):
    
    if json_data is None: raise dash.exceptions.PreventUpdate

    ctx = callback_context
    if not ctx.triggered: raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df = parse_data(json_data)
    msg = ""
    alert_type = "alert alert-success"

    try:
        # --- MISSING VALUES ---
        if button_id == 'btn-apply-missing':
            if not miss_col: return dash.no_update, html.Div("Select a column.", className="alert alert-danger")

            if miss_action == 'drop_rows':
                df = df.dropna(subset=[miss_col])
                msg = f"Dropped rows missing in '{miss_col}'"
            elif miss_action == 'mean':
                if pd.api.types.is_numeric_dtype(df[miss_col]):
                    df[miss_col] = df[miss_col].fillna(df[miss_col].mean())
                    msg = f"Filled '{miss_col}' with Mean"
                else:
                    return dash.no_update, html.Div(f"'{miss_col}' is not numeric. Convert it in 'Data Types' tab first.", className="alert alert-warning")
            elif miss_action == 'median':
                if pd.api.types.is_numeric_dtype(df[miss_col]):
                    df[miss_col] = df[miss_col].fillna(df[miss_col].median())
                    msg = f"Filled '{miss_col}' with Median"
                else:
                    return dash.no_update, html.Div(f"'{miss_col}' is not numeric. Convert it in 'Data Types' tab first.", className="alert alert-warning")
            elif miss_action == 'mode':
                 df[miss_col] = df[miss_col].fillna(df[miss_col].mode()[0])
                 msg = f"Filled '{miss_col}' with Mode"

        # --- DATA TYPES ---
        elif button_id == 'btn-apply-type':
            if not type_col: return dash.no_update, html.Div("Select a column.", className="alert alert-danger")
            
            if type_target == 'numeric':
                df[type_col] = pd.to_numeric(df[type_col], errors='coerce')
                msg = f"Converted '{type_col}' to Numeric"
            elif type_target == 'string':
                df[type_col] = df[type_col].astype(str)
                msg = f"Converted '{type_col}' to String"
            elif type_target == 'datetime':
                df[type_col] = pd.to_datetime(df[type_col], errors='coerce')
                msg = f"Converted '{type_col}' to Datetime"

        # --- DROP COLUMNS ---
        elif button_id == 'btn-apply-drop':
            if not drop_cols: return dash.no_update, html.Div("Select columns.", className="alert alert-danger")
            df = df.drop(columns=drop_cols)
            msg = f"Dropped columns: {', '.join(drop_cols)}"

        return df.to_json(date_format='iso', orient='split'), html.Div(f"✅ {msg}", className=alert_type)

    except Exception as e:
        return dash.no_update, html.Div(f"Error: {e}", className="alert alert-danger")

# --- Callback 4: Download Data ---
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download", "n_clicks"),
    State("stored-data", "data"),
    prevent_initial_call=True
)
def download_csv(n_clicks, json_data):
    if json_data is None: return dash.no_update
    
    df = parse_data(json_data)
    if df is None: return dash.no_update

    # Generate CSV
    return dcc.send_data_frame(df.to_csv, "cleaned_data.csv", index=False)
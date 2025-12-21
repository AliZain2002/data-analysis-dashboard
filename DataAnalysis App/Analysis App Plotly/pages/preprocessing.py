from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import dash
import io
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler, LabelEncoder

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
    
    # Header & Global Download
    html.Div([
        html.H2("🛠️ Data Preprocessing", style={'display': 'inline-block', 'marginRight': '20px'}),
        dcc.Download(id="download-dataframe-csv"),
        html.Button("📥 Download Current Dataset", id="btn-download", className="btn btn-success", style={'verticalAlign': 'top'})
    ], style={'marginBottom': '10px'}),

    html.P("Clean, Transform, and Prepare your dataset for Analysis or ML."),
    html.Hr(),

    # Alert Box for Status Messages
    html.Div(id='preprocessing-alert'),

    # --- TABS ---
    dcc.Tabs(id="preprocessing-tabs", value='tab-info', children=[
        dcc.Tab(label='1. Info', value='tab-info'),
        dcc.Tab(label='2. Missing Values', value='tab-missing'),
        dcc.Tab(label='3. Data Types', value='tab-types'),
        dcc.Tab(label='4. Drop Columns', value='tab-columns'),
        dcc.Tab(label='5. Clean Categories', value='tab-clean-cat'),
        dcc.Tab(label='6. Discretize', value='tab-discretize'),
        dcc.Tab(label='7. Normalize', value='tab-normalize'),
        dcc.Tab(label='8. Encode', value='tab-encode'),
        dcc.Tab(label='9. Split Data', value='tab-split'),
    ]),

    # --- TAB CONTENT AREAS (Defined Statically) ---
    
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
                {'label': 'Drop Rows', 'value': 'drop_rows'},
                {'label': 'Fill Mean (Numeric)', 'value': 'mean'},
                {'label': 'Fill Median (Numeric)', 'value': 'median'},
                {'label': 'Fill Mode (Frequent)', 'value': 'mode'},
                {'label': 'Fill Forward (Value Above)', 'value': 'ffill'}, # NEW
                {'label': 'Fill Backward (Value Below)', 'value': 'bfill'} # NEW
            ],
            value='drop_rows'
        ),
        html.Br(),
        html.Button("Apply Treatment", id='btn-apply-missing', className="btn btn-primary")
    ]),

    # 3. Data Types Tab
    html.Div(id='content-types', style={'display': 'none'}, children=[
        html.H5("Change Data Types"),
        html.P("Convert columns to specific types. Bad values (e.g., 'aa' in numbers) will become NaN.", className="text-muted"),
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

    # 4. Drop Columns Tab
    html.Div(id='content-columns', style={'display': 'none'}, children=[
        html.H5("Drop Columns"),
        dcc.Dropdown(id='drop-col-dropdown', multi=True, placeholder="Select columns to remove..."),
        html.Br(),
        html.Button("Drop Selected Columns", id='btn-apply-drop', className="btn btn-danger")
    ]),

    # 5. Clean Categories Tab
    html.Div(id='content-clean-cat', style={'display': 'none'}, children=[
        html.H5("Value Replacement (Fix Typos)"),
        html.P("Replace specific values (e.g., change '12' to 'Male' in Gender)."),
        
        html.Div(className='row', children=[
            html.Div(className='col-md-6', children=[
                html.Label("1. Select Column to Inspect:"),
                dcc.Dropdown(id='clean-cat-col-dropdown', placeholder="Select categorical column..."),
                html.Br(),
                html.Label("Current Value Counts:"),
                html.Div(id='clean-cat-value-counts')
            ]),
            html.Div(className='col-md-6', children=[
                html.Label("2. Select Value to Replace:"),
                dcc.Dropdown(id='clean-cat-bad-value', placeholder="Choose the bad value..."),
                html.Br(),
                html.Label("3. Enter Correct Value:"),
                dcc.Input(id='clean-cat-new-value', type='text', placeholder="Type correct value...", className='form-control'),
                html.Br(), html.Br(),
                html.Button("Replace Value", id='btn-apply-replace', className="btn btn-primary")
            ])
        ])
    ]),

    # 6. Discretize Tab
    html.Div(id='content-discretize', style={'display': 'none'}, children=[
        html.H5("Discretization (Binning)"),
        html.P("Group continuous numbers into bins (e.g., Income -> Income Groups)."),
        html.Label("Select Numeric Column:"),
        dcc.Dropdown(id='disc-col-dropdown', placeholder="Select numeric column..."),
        html.Br(),
        html.Label("Number of Bins:"),
        dcc.Input(id='disc-bins-input', type='number', value=5, min=2, className='form-control'),
        html.Br(), html.Br(),
        dcc.RadioItems(
            id='disc-strategy',
            options=[{'label': 'Equal Width', 'value': 'uniform'}, {'label': 'Equal Frequency (Quantile)', 'value': 'quantile'}],
            value='uniform'
        ),
        html.Br(),
        html.Button("Apply Binning", id='btn-apply-disc', className="btn btn-primary")
    ]),

    # 7. Normalize Tab
    html.Div(id='content-normalize', style={'display': 'none'}, children=[
        html.H5("Normalization / Scaling"),
        html.P("Scale numeric data to a specific range (essential for ML)."),
        dcc.Dropdown(id='norm-col-dropdown', multi=True, placeholder="Select numeric columns..."),
        html.Br(),
        dcc.RadioItems(
            id='norm-method',
            options=[
                {'label': 'Min-Max Scaling (0-1)', 'value': 'minmax'},
                {'label': 'Standard Scaling (Z-Score)', 'value': 'standard'},
                {'label': 'Robust Scaling (Outlier Safe)', 'value': 'robust'}
            ],
            value='minmax'
        ),
        html.Br(),
        html.Button("Apply Normalization", id='btn-apply-norm', className="btn btn-primary")
    ]),

    # 8. Encode Tab
    html.Div(id='content-encode', style={'display': 'none'}, children=[
        html.H5("Categorical Encoding"),
        html.P("Convert text categories into numbers."),
        dcc.Dropdown(id='enc-col-dropdown', placeholder="Select categorical column..."),
        html.Br(),
        dcc.RadioItems(
            id='enc-method',
            options=[
                {'label': 'One-Hot Encoding (Dummy Variables)', 'value': 'onehot'},
                {'label': 'Label Encoding (0, 1, 2...)', 'value': 'label'}
            ],
            value='onehot'
        ),
        html.Br(),
        html.Button("Apply Encoding", id='btn-apply-enc', className="btn btn-primary")
    ]),

    # 9. Split Tab
    html.Div(id='content-split', style={'display': 'none'}, children=[
        html.H5("Train-Test Split"),
        html.P("Split data for Machine Learning training."),
        html.Label("Target Variable (Y):"),
        dcc.Dropdown(id='split-target-dropdown', placeholder="Select target column..."),
        html.Br(),
        html.Label("Test Set Size:"),
        dcc.Slider(id='split-size-slider', min=0.1, max=0.5, step=0.05, value=0.2, 
                   marks={0.1: '10%', 0.2: '20%', 0.3: '30%', 0.4: '40%', 0.5: '50%'}),
        html.Br(),
        html.Div([
            dcc.Download(id="download-train-csv"),
            dcc.Download(id="download-test-csv"),
            html.Button("✂️ Split & Download CSVs", id="btn-apply-split", className="btn btn-success")
        ])
    ])
])

# --- CALL BACKS ---

# 1. Tab Visibility Logic
@app.callback(
    [Output(f'content-{name}', 'style') for name in ['info', 'missing', 'types', 'columns', 'clean-cat', 'discretize', 'normalize', 'encode', 'split']],
    [Input('preprocessing-tabs', 'value')]
)
def tab_visibility(tab):
    tabs = ['tab-info', 'tab-missing', 'tab-types', 'tab-columns', 'tab-clean-cat', 'tab-discretize', 'tab-normalize', 'tab-encode', 'tab-split']
    return [{'display': 'block', 'padding': '20px', 'border': '1px solid #ddd', 'borderTop': 'none'} if tab == t else {'display': 'none'} for t in tabs]

# 2. Populate Dropdowns & Info Table
@app.callback(
    [Output('data-summary-table', 'children'),
     Output('missing-col-dropdown', 'options'),
     Output('type-col-dropdown', 'options'),
     Output('drop-col-dropdown', 'options'),
     Output('clean-cat-col-dropdown', 'options'),
     Output('disc-col-dropdown', 'options'),
     Output('norm-col-dropdown', 'options'),
     Output('enc-col-dropdown', 'options'),
     Output('split-target-dropdown', 'options')],
    [Input('stored-data', 'data')]
)
def populate_options(json_data):
    if json_data is None: return html.Div("Please upload data first."), [], [], [], [], [], [], [], []
    
    df = parse_data(json_data)
    if df is None: return html.Div("Error loading data."), [], [], [], [], [], [], [], []
    
    # Info Table
    summary = pd.DataFrame({'Column': df.columns, 'Type': df.dtypes.astype(str), 'Nulls': df.isnull().sum()})
    info_table = html.Div([
        html.H5(f"Dataset Shape: {df.shape[0]} Rows, {df.shape[1]} Columns"),
        dash_table.DataTable(data=summary.to_dict('records'), columns=[{'name': i, 'id': i} for i in summary.columns], page_size=10, style_table={'overflowX': 'auto'})
    ])

    all_cols = [{'label': c, 'value': c} for c in df.columns]
    num_cols = [{'label': c, 'value': c} for c in df.select_dtypes(include=np.number).columns]
    cat_cols = [{'label': c, 'value': c} for c in df.select_dtypes(exclude=np.number).columns]
    
    return info_table, all_cols, all_cols, all_cols, all_cols, num_cols, num_cols, cat_cols, all_cols

# 3. Populate "Clean Categories" Specific Options (With FIX)
@app.callback(
    [Output('clean-cat-value-counts', 'children'),
     Output('clean-cat-bad-value', 'options')],
    [Input('clean-cat-col-dropdown', 'value'),
     Input('stored-data', 'data')]
)
def update_clean_cat_options(col, json_data):
    if json_data is None or col is None: return "", []
    df = parse_data(json_data)
    
    # Value Counts Table
    counts = df[col].value_counts().reset_index()
    counts.columns = ['Value', 'Count']
    table = dash_table.DataTable(
        data=counts.to_dict('records'), 
        columns=[{'name': i, 'id': i} for i in counts.columns], 
        page_size=5,
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
    )
    
    # Dropdown Options (Filter out Nulls to fix Dash error)
    unique_vals = df[col].unique()
    options = [{'label': str(val), 'value': val} for val in unique_vals if pd.notnull(val)]
    
    return table, options

# 4. MAIN PROCESSING LOGIC
@app.callback(
    [Output('stored-data', 'data', allow_duplicate=True),
     Output('preprocessing-alert', 'children')],
    [Input('btn-apply-missing', 'n_clicks'),
     Input('btn-apply-type', 'n_clicks'),
     Input('btn-apply-drop', 'n_clicks'),
     Input('btn-apply-replace', 'n_clicks'),
     Input('btn-apply-disc', 'n_clicks'),
     Input('btn-apply-norm', 'n_clicks'),
     Input('btn-apply-enc', 'n_clicks')],
    [State('stored-data', 'data'),
     State('missing-col-dropdown', 'value'), State('missing-action-radio', 'value'),
     State('type-col-dropdown', 'value'), State('type-target-dropdown', 'value'),
     State('drop-col-dropdown', 'value'),
     State('clean-cat-col-dropdown', 'value'), State('clean-cat-bad-value', 'value'), State('clean-cat-new-value', 'value'),
     State('disc-col-dropdown', 'value'), State('disc-bins-input', 'value'), State('disc-strategy', 'value'),
     State('norm-col-dropdown', 'value'), State('norm-method', 'value'),
     State('enc-col-dropdown', 'value'), State('enc-method', 'value')],
    prevent_initial_call=True
)
def process_data(b1, b2, b3, b4, b5, b6, b7, json_data,
                 miss_col, miss_action,
                 type_col, type_target,
                 drop_cols,
                 clean_col, bad_val, new_val,
                 disc_col, disc_bins, disc_strat,
                 norm_cols, norm_method,
                 enc_col, enc_method):
    
    if json_data is None: raise dash.exceptions.PreventUpdate
    ctx = callback_context
    if not ctx.triggered: raise dash.exceptions.PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df = parse_data(json_data)
    msg = ""
    alert_type = "alert alert-success"

    try:
        # 1. Missing Values (UPDATED WITH FFILL/BFILL)
        if button_id == 'btn-apply-missing':
            if miss_action == 'drop_rows': df.dropna(subset=[miss_col], inplace=True)
            elif miss_action == 'mean': 
                if pd.api.types.is_numeric_dtype(df[miss_col]): df[miss_col].fillna(df[miss_col].mean(), inplace=True)
                else: return dash.no_update, html.Div("Column is not numeric. Convert type first.", className="alert alert-warning")
            elif miss_action == 'median':
                if pd.api.types.is_numeric_dtype(df[miss_col]): df[miss_col].fillna(df[miss_col].median(), inplace=True)
                else: return dash.no_update, html.Div("Column is not numeric. Convert type first.", className="alert alert-warning")
            elif miss_action == 'mode': df[miss_col].fillna(df[miss_col].mode()[0], inplace=True)
            elif miss_action == 'ffill':
                df[miss_col] = df[miss_col].ffill()
                msg = f"Filled {miss_col} with value above (Forward Fill)"
            elif miss_action == 'bfill':
                df[miss_col] = df[miss_col].bfill()
                msg = f"Filled {miss_col} with value below (Backward Fill)"
            
            if not msg: msg = f"Applied {miss_action} to {miss_col}"

        # 2. Types
        elif button_id == 'btn-apply-type':
            if type_target == 'numeric': df[type_col] = pd.to_numeric(df[type_col], errors='coerce')
            elif type_target == 'string': df[type_col] = df[type_col].astype(str)
            elif type_target == 'datetime': df[type_col] = pd.to_datetime(df[type_col], errors='coerce')
            msg = f"Converted {type_col} to {type_target}"

        # 3. Drop
        elif button_id == 'btn-apply-drop':
            df.drop(columns=drop_cols, inplace=True)
            msg = f"Dropped columns: {len(drop_cols)}"

        # 4. Clean Categories (Replace Value)
        elif button_id == 'btn-apply-replace':
            if clean_col and bad_val is not None:
                df[clean_col] = df[clean_col].replace(bad_val, new_val)
                msg = f"Replaced '{bad_val}' with '{new_val}' in {clean_col}"
            else:
                return dash.no_update, html.Div("Please select value to replace.", className="alert alert-danger")

        # 5. Discretize
        elif button_id == 'btn-apply-disc':
            new_col = f"{disc_col}_bins"
            if disc_strat == 'uniform': df[new_col] = pd.cut(df[disc_col], bins=disc_bins, labels=False)
            else: df[new_col] = pd.qcut(df[disc_col], q=disc_bins, labels=False, duplicates='drop')
            msg = f"Binned {disc_col}"

        # 6. Normalize
        elif button_id == 'btn-apply-norm':
            if norm_method == 'minmax': scaler = MinMaxScaler()
            elif norm_method == 'standard': scaler = StandardScaler()
            elif norm_method == 'robust': scaler = RobustScaler()
            df[norm_cols] = scaler.fit_transform(df[norm_cols])
            msg = f"Normalized {len(norm_cols)} columns using {norm_method}"

        # 7. Encode
        elif button_id == 'btn-apply-enc':
            if enc_method == 'label':
                df[enc_col] = LabelEncoder().fit_transform(df[enc_col].astype(str))
                msg = f"Label Encoded {enc_col}"
            elif enc_method == 'onehot':
                dummies = pd.get_dummies(df[enc_col], prefix=enc_col, dtype=int)
                df = pd.concat([df, dummies], axis=1)
                msg = f"One-Hot Encoded {enc_col}"

        return df.to_json(date_format='iso', orient='split'), html.Div(f"✅ {msg}", className=alert_type)

    except Exception as e:
        return dash.no_update, html.Div(f"Error: {e}", className="alert alert-danger")

# 5. Download Callback
@app.callback(
    [Output("download-dataframe-csv", "data"), 
     Output("download-train-csv", "data"), 
     Output("download-test-csv", "data")],
    [Input("btn-download", "n_clicks"), 
     Input("btn-apply-split", "n_clicks")],
    [State("stored-data", "data"), 
     State("split-target-dropdown", "value"), 
     State("split-size-slider", "value")],
    prevent_initial_call=True
)
def handle_downloads(b1, b2, json_data, target, size):
    ctx = callback_context
    if not ctx.triggered or json_data is None: return None, None, None
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    df = parse_data(json_data)
    
    if btn == "btn-download":
        return dcc.send_data_frame(df.to_csv, "cleaned_dataset.csv", index=False), None, None
    
    if btn == "btn-apply-split":
        if not target: return None, None, None
        try:
            train, test = train_test_split(df, test_size=size, random_state=42)
            return None, dcc.send_data_frame(train.to_csv, "train.csv", index=False), dcc.send_data_frame(test.to_csv, "test.csv", index=False)
        except Exception as e:
            print(e)
            return None, None, None
            
    return None, None, None
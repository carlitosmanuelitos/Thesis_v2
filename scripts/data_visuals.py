import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import pandas as pd
from glob import glob

# Get unique identifiers for dropdown options
def get_dropdown_options():
    files = glob('data/*/*-USD_*_*.csv')
    tickers = set()
    periods = set()
    intervals = set()
    dates = set()

    for file in files:
        path_parts = file.split(os.sep)
        ticker = path_parts[1]
        filename = path_parts[-1].split('_')
        period, interval, date = filename[1], filename[2], filename[3].split('.')[0]

        tickers.add(ticker)
        periods.add(period)
        intervals.add(interval)
        dates.add(date)
    
    return {
        'tickers': [{'label': ticker, 'value': ticker} for ticker in sorted(tickers)],
        'periods': [{'label': period, 'value': period} for period in sorted(periods)],
        'intervals': [{'label': interval, 'value': interval} for interval in sorted(intervals)],
        'dates': [{'label': date, 'value': date} for date in sorted(dates, reverse=True)]
    }

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Expose server for deployments

# Populate dropdown options
dropdown_options = get_dropdown_options()

# Set up the Dash app layout with tabs and subplots
app.layout = html.Div([
    html.H1('Cryptocurrency Data Visualization', style={'textAlign': 'center'}),
    html.Div([
        dcc.Dropdown(
            id='ticker-dropdown',
            options=dropdown_options['tickers'],
            value='BTC',  # Default value
            style={'width': '24%', 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='period-dropdown',
            options=dropdown_options['periods'],
            value='1y',  # Default value
            style={'width': '24%', 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='interval-dropdown',
            options=dropdown_options['intervals'],
            value='1d',  # Default value
            style={'width': '24%', 'display': 'inline-block'}
        ),
        dcc.Dropdown(
            id='date-dropdown',
            options=dropdown_options['dates'],
            value=dropdown_options['dates'][0]['value'],  # Default to most recent date
            style={'width': '24%', 'display': 'inline-block'}
        ),
    ], style={'padding': '10px', 'background': '#CCCCCC'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Tab One', value='tab-1'),
        dcc.Tab(label='Tab Two', value='tab-2'),
    ]),
    html.Div(id='tabs-content')
])

# Callback to update each graph based on dropdown selection
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dcc.Graph(id='candlestick-chart'),
            dcc.Graph(id='trend-chart'),
            dcc.Graph(id='volume-chart'),
            dcc.Graph(id='macd-chart'),
        ], style={'display': 'grid', 'grid-template-columns': '1fr 1fr', 'gap': '10px'})
    elif tab == 'tab-2':
        return html.Div([
            dcc.Graph(id='rsi-chart'),
            dcc.Graph(id='fibonacci-chart'),
            dcc.Graph(id='bollinger-chart'),
        ], style={'display': 'grid', 'grid-template-columns': '1fr 1fr', 'gap': '10px'})

# Define callbacks for updating graphs based on user input...
# (You will need to implement these based on the financial calculations for each indicator)

if __name__ == '__main__':
    app.run_server(debug=True)
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
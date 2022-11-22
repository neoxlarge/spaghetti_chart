import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
import pandas as pd
import plotly.graph_objs as go
import flask
import waitress
from waitress import serve


server = flask.Flask(__name__) # define flask app.server

app = dash.Dash(__name__, server=server) # call flask server
    

app.layout = html.Div(
    html.Div([
        dcc.Graph(id='live-update-graph-scatter', animate=True),
        dcc.Interval(
            id='interval-component',
            disabled=False,
            interval=1*5000,
            n_intervals=0
        )
    ])
)

@app.callback(Output('live-update-graph-scatter', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_scatter(n):


    rec = pd.read_sql_table('crypto', engine)
    rec1 = pd.DataFrame(rec)
    print(rec1)
    rec1.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'EMA', 'EMA2']

    rec1['date'] = pd.to_datetime(rec1['date'])
    rec1.set_index('date', inplace=True)

    ###SUBPLOT AND Candlestick CHART
    fig = make_subplots(rows=4, cols=1)

    fig.add_trace(go.Candlestick(
        x=rec1.index,
        open=rec1['open'],
        high=rec1['high'],
        low=rec1['low'],
        close=rec1['close']),
        row=1,
        col=1,
    )

    ###### ADD INDICATOR TRACES:
    fig.add_trace(
        go.Scatter(
            x=rec1.index,
            y=rec1['EMA'],
            marker=dict(color='blue')
        ),
        row=1,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=rec1.index,
            y=rec1['EMA2'],
            marker=dict(color='red')
        ),
        row=1,
        col=1
    )



    return fig



if __name__ == '__main__':
    serve(app.server, host="localhost", port=5005)
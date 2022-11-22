import dash
from dash import dcc
from dash import html
import plotly.graph_objects as px


#html
html_list = []

html_list.append(html.H1("hello"))

for i in range(100):
    html_list.append(html.Button(i,id=f"{i}"))

app = dash.Dash(__name__)


app.layout = html.Div(html_list)


if __name__ == "__main__":
    app.run_server(debug=True)
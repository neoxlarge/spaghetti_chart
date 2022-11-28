
from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],use_pages=True)

pages_link = [html.Div(dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"]))
            for page in dash.page_registry.values()]

app.layout = html.Div([
	html.H5("Spaghetti Chart by neoxbitcoin"),

    html.Div(pages_link),

	dash.page_container
])

if __name__ == '__main__':
	app.run_server(port = 8080, host='0.0.0.0',debug=True)
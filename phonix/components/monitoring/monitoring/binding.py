from dash import Dash, dcc, html
from dash.dependencies import Input, Output

def create_dash_app(plot_interface, route_prefix='/phonix-monitor/'):
    dash_app = Dash(
        __name__,
        routes_pathname_prefix=route_prefix,
    )

    dash_app.layout = html.Div([
        dcc.Graph(id='live-graph'),
        dcc.Interval(id='interval', interval=1000, n_intervals=0)
    ])

    @dash_app.callback(Output('live-graph', 'figure'), Input('interval', 'n_intervals'))
    def update_graph(n):
        return plot_interface.get_figure()

    return dash_app

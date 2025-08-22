from dash import Dash, dcc, html
from dash.dependencies import Input, Output

def create_dash_app(plot_interface, route_prefix):
    dash_app = Dash(__name__, routes_pathname_prefix=route_prefix)

    dash_app.layout = html.Div(
        style={"height": "100vh", "margin": 0},  # контейнер на всю высоту окна
        children=[
            dcc.Graph(
                id='live-graph',
                style={"height": "100%", "width": "100%"},  # график заполняет контейнер
                config={"responsive": True},
            ),
            dcc.Interval(id='interval', interval=1000, n_intervals=0),
        ]
    )

    @dash_app.callback(Output('live-graph', 'figure'), Input('interval', 'n_intervals'))
    def update_graph(n):
        fig = plot_interface.get_figure()
        fig.update_layout(autosize=True)  # без фиксированного height
        return fig

    return dash_app

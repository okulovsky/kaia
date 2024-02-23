from kaia.bro.core import PlotMethod
from plotly import graph_objects as go



class Plot(PlotMethod):
    def draw(self, df, name):
        max_timestamp = df.timestamp.max()
        df['delta_t'] = (max_timestamp - df.timestamp)
        df = df.loc[df.delta_t.dt.total_seconds() < 3*24*60*60].copy()

        df = df.drop_duplicates('timestamp').sort_values('timestamp')

        traces = []

        traces.append(go.Scatter(
            x=df.timestamp,
            y=df.switch_state,
            name='Switch state',
            line=dict(color='gray', width=2),
        ))

        traces.append(go.Scatter(
            x=df.loc[~df.switch_request.isnull() & (df.switch_request==True)].timestamp,
            y=df.loc[~df.switch_request.isnull() & (df.switch_request==True)].switch_state,
            mode='markers',
            name='on',
            marker=dict(size=10, color='green')
        ))

        traces.append(go.Scatter(
            x=df.loc[~df.switch_request.isnull() & (df.switch_request==False)].timestamp,
            y=df.loc[~df.switch_request.isnull() & (df.switch_request==False)].switch_state,
            mode='markers',
            name='off',
            marker=dict(size=10, color='red')
        ))

        layout = go.Layout(
            title=name,
            yaxis=dict(title='state'),
        )

        return go.Figure(data=traces, layout=layout)

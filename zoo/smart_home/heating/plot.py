from plotly import graph_objects as go
import numpy as np
import pandas as pd


def draw(df):
    max_timestamp = df.timestamp.max()
    df['delta_t'] = (max_timestamp - df.timestamp)
    df = df.loc[df.delta_t.dt.total_seconds() < 3*24*60*60].copy()

    df = df.drop_duplicates('timestamp').sort_values('timestamp')

    traces = []
    traces.append(go.Scatter(
        x=df.timestamp,
        y=df.temperature_on_sensor,
        name='T at sensor',
        line=dict(color='red', width=2),
        yaxis='y1'
    ))
    traces.append(go.Scatter(
        x=df.timestamp,
        y=df.temperature_setpoint,
        name='setup',
        line=dict(color='blue', width=2),
        yaxis='y1'
    ))
    traces.append(go.Scatter(
        x=df.timestamp,
        y=df.temperature_on_thermostat,
        name='T at thermostat',
        line=dict(color='orange', width=2),
        yaxis='y1'
    ))
    traces.append(go.Scatter(
        x=df.timestamp,
        y=df.valve_position,
        name='valve position',
        line=dict(color='gray', width=1, dash='dash'),
        yaxis='y2'
    ))

    layout = go.Layout(title='Dehumidifier',
                       yaxis=dict(title='Temperature'),
                       yaxis2=dict(title='Valve position', overlaying='y', side='right'))
    return go.Figure(data=traces, layout=layout)

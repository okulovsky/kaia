import os

from plotly import graph_objects as go
import numpy as np
import pandas as pd
from kaia.infra import Loc
from datetime import datetime

def get_shifter(series):
    return series | series.shift(-1)


def draw(df):
    #debug_folder = Loc.data_folder/'debug'
    #os.makedirs(debug_folder, exist_ok=True)
    #df.to_parquet(debug_folder/str(datetime.now()))

    max_timestamp = df.timestamp.max()
    df['delta_t'] = (max_timestamp - df.timestamp)
    df = df.loc[df.delta_t.dt.total_seconds() < 3*24*60*60].copy()

    df = df.drop_duplicates('timestamp').sort_values('timestamp')

    df['hum_on'] = pd.Series(np.where(get_shifter(df.state),df.humidity, None), index=df.index)
    df['hum_off'] = pd.Series(np.where(get_shifter(~df.state),df.humidity, None), index=df.index)


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.hum_on, name='on', line=dict(color='red', width=2)))
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.hum_off, name='off', line=dict(color='blue',width=2)))
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.low_humidity, name='low', line=dict(color='gray', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.high_humidity, name='high', line=dict(color='gray', width=1, dash='dash')))

    for val in df.loc[~df.state_request_reason.isnull()].state_request_reason.unique():
        if val is None:
            continue
        line = np.where(df.state_request_reason==val, df.humidity, None)
        fig.add_trace(go.Scatter(x=df.timestamp, y=line, mode='markers', name=val, marker=dict(size=10)))

    return fig

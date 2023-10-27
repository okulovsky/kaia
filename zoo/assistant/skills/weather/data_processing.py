import pandas as pd
from datetime import timedelta, date
from .dubs import DayPeriods, Replies
from yo_fluq_ds import *


periods_definitions = {
    DayPeriods.Night: [0,1,2,3,4,5,6,7],
    DayPeriods.Morning: [8,9,10,11, 12],
    DayPeriods.Afternoon: [13,14,15,16,17],
    DayPeriods.Evening: [18,19,20,21,22,23]
}

def reply_to_df(reply):
    periods = {hour: period for period in periods_definitions for hour in periods_definitions[period]}
    assert tuple(sorted(periods)) == tuple(range(24))

    df = pd.DataFrame(reply['hourly'])
    df.time = pd.to_datetime(df.time)

    df['period'] = df.time.dt.hour.map(periods)
    df['date'] = df.time.dt.date
    next_night = df.period==DayPeriods.Night
    df.loc[next_night, 'date'] = df.loc[next_night, 'date'] + timedelta(days=1)
    df = df.merge(df.groupby(['date','period']).size().to_frame('period_size'), left_on=['date', 'period'], right_index=True)
    df = df.loc[df.period_size>3]
    return df


def df_to_forecast_df(df):
    wdf = df.groupby(['date', 'period', 'weathercode']).size().to_frame('cnt').reset_index()
    wdf = wdf.merge(df.groupby(['date', 'period']).size().to_frame('total'), left_on=['date', 'period'],
                    right_index=True)
    wdf['frac'] = wdf.cnt / wdf.total
    wdf = wdf.feed(fluq.add_ordering_column(['date', 'period'], ('cnt', False)))
    wdf = wdf.loc[wdf.order <= 2]
    wdf = wdf.rename(columns={'weathercode': 'wc'})
    wdf = wdf.pivot_table(index=['date', 'period'], columns='order', values=['wc', 'frac'])
    wdf.columns = [f'{c[0]}_{c[1]}' for c in wdf.columns]
    for c in wdf.columns:
        wdf[c] = wdf[c].fillna(-1).astype(int) if c.startswith('wc') else wdf[c].fillna(0)
    wdf = wdf.reset_index()

    tdf = df.groupby(['date', 'period']).temperature_2m.aggregate(['min', 'max'])
    tdf = tdf.rename(columns=dict(min='low_temp', max='high_temp'))
    wdf = wdf.merge(tdf, left_on=['date', 'period'], right_index=True)
    return wdf


class ForecastBuilder:
    def __init__(self):
        self.forecast = {}

    def observe(self, period):
        code = {}
        if period.wc_1 == -1:
            code['wc'] = period.wc_0
        elif period.wc_2 == -1:
            if period.frac_0 > 0.5:
                code['high_wc'] = period.wc_0
                code['wc'] = period.wc_1
            else:
                code['wc'] = period.wc_0
                code['wc_1'] = period.wc_1
        else:
            if period.frac_0 > 0.5:
                code['high_wc'] = period.wc_0
                code['wc'] = period.wc_1
                code['wc_1'] = period.wc_2
            else:
                code['wc'] = period.wc_0
                code['wc_1'] = period.wc_1
                code['wc_2'] = period.wc_2

        temperature = dict(low_temp=int(period['low_temp']), high_temp=int(period['high_temp']))

        if period.date not in self.forecast:
            self.forecast[period.date] = {}
        self.forecast[period.date][period.period] = dict(code=code, temperature=temperature)

    @staticmethod
    def build_from_wdf(wdf):
        bld = ForecastBuilder()
        Query.df(wdf).foreach(bld.observe)
        return bld.forecast


def to_utterances(forecast: Dict[date, Dict[DayPeriods,Dict]]):
    result = []
    for index, date in enumerate(sorted(forecast)):
        opening = Replies.forecast_first_day if index == 0 else Replies.forecast_following_days
        result.append(opening.utter(relative_day=date, date=date))
        for period in sorted(forecast[date]):
            result.append(Replies.day_period.utter(period = period))
            fc = forecast[date][period]
            result.append(Replies.temperature.utter(**fc['temperature']))
            result.append(Replies.weather_code.utter(**fc['code']))
    return result


def make_all(reply):
    df = reply_to_df(reply)
    wdf = df_to_forecast_df(df)
    forecast = ForecastBuilder.build_from_wdf(wdf)
    utterances = to_utterances(forecast)
    return utterances

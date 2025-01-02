import pandas as pd

from ....job_processing import Job
from .batch_page import _select, _pretty_sec
from sqlalchemy import select, case, func
from yo_fluq import *
import numpy as np

def _get_frames(session):
    cte = _select().cte('processed_jobs')

    status_query = (
        session.query(
            cte.c.batch,
            cte.c.status,
            func.count(cte.c.id).label("count"),
        ).group_by(cte.c.batch, cte.c.status)
    )

    stats_query = (
        session.query(
            cte.c.batch,
            func.min(cte.c.received_timestamp).label('received_timestamp'),
            func.max(cte.c.finished_timestamp).label('finished_timestamp'),
            func.avg(cte.c.in_work).label('processing_time'),
            func.sum(cte.c.in_work).label('total_processing_time'),
            func.avg(cte.c.progress).label('progress'),
        ).group_by(cte.c.batch)
    )

    names_query = (
        session.query(
            cte.c.batch,
            cte.c.decider,
            func.count(cte.c.id).label('amount')
        ).group_by(cte.c.batch, cte.c.decider)
    )

    df_status = pd.read_sql_query(status_query.statement, session.bind)
    df_stats = pd.read_sql_query(stats_query.statement, session.bind)
    df_names = pd.read_sql_query(names_query.statement, session.bind)

    return df_status, df_stats, df_names


def _get_merged_frame(df_status, df_stats, df_names):
    if df_status.shape[0] == 0:
        return None
    df = df_status
    df = df.pivot_table(index='batch', columns='status', values='count').fillna(0)
    for column in ['success','in_work','failure','waiting']:
        if column not in df.columns:
            df[column] = 0
    df['total'] = df.sum(axis=1)
    df['finished'] = df.success + df.failure
    df = df.astype(int)
    df.columns = ['tasks_' + c for c in df.columns]
    df['is_finished'] = df.tasks_finished == df.tasks_total

    df = df_stats.merge(df, right_index=True, left_on='batch')

    df_names['part'] = df_names['decider'] + ' x ' + df_names['amount'].astype(str) + "\n"
    names = df_names.groupby('batch').part.sum()
    df = df.merge(names.to_frame('names'), left_on='batch', right_index=True)

    df = df.sort_values('received_timestamp', ascending=False)

    pd.options.display.width = None
    return df

def _to_html(df):
    html = []

    for row in Query.df(df.reset_index()):
        html.append('<tr>')
        html.append(f'<td><a href="/html/jobs/batch_page/{row.batch}">{row.batch}</td>')
        names = "<br>".join([z for z in row.names.split('\n') if z!=''])
        html.append(f'<td>{names}</td>')
        eta = None
        if row.tasks_total == 1:
            progress = row.progress
            if progress is not None and progress > 0:
                eta = row.processing_time * (1 - progress) / progress
        else:
            progress = row.tasks_finished / row.tasks_total
            if row.processing_time is not None:
                eta = row.processing_time * (row.tasks_total - row.tasks_finished)

        html.append(f'<td>{row.received_timestamp}</td>')

        html.append('<td>')
        if row.is_finished:
            html.append(str(row.finished_timestamp))
            if row.total_processing_time is not None:
                html.append("<br>")
                html.append(_pretty_sec(row.total_processing_time))
        else:
            if progress is not None and not np.isnan(progress):
                html.append(f'{int(100 * progress)}%')
                if eta is not None:
                    html.append(f'<br>{_pretty_sec(eta)}')
            else:
                html.append('?')
        html.append("</td>")


    return ''.join(html)


def create_main_page(session):
    df = _get_merged_frame(*_get_frames(session))
    if df is None:
        html = ''
    else:
        html = _to_html(df)
    return f'''
<html><body>
[<a href="/html/jobs/operator_log">Operator log</a>]&nbsp;[<a href="/html/controllers/status">Controllers</a>]</br>
<table border=1 cellspacing=0>
{html}
</table></body></html>'
'''

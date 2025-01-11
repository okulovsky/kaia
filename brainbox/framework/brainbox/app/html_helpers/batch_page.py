from datetime import datetime

import numpy as np

from ....job_processing import Job
from sqlalchemy.orm import Session
from sqlalchemy import select, case, func
from yo_fluq import *

def _calculate_julian_date(dt: datetime):
    julian_date = dt.toordinal() + 1721425.5
    return julian_date

def _select():
    query = select(
        Job.id,
        Job.batch,
        case((
            Job.method.isnot(None),
            Job.decider + ':' + Job.method),
            else_=Job.decider
        ).label("decider"),
        Job.received_timestamp,
        Job.accepted_timestamp,
        Job.finished_timestamp,
        (
                (func.julianday(Job.accepted_timestamp) -
                 func.julianday(Job.received_timestamp)
                 ) * 86400
        ).label('in_queue'),
        case(
            (
                Job.finished,
                (
                        func.julianday(Job.finished_timestamp) -
                        func.julianday(Job.accepted_timestamp)
                ) * 86400,
            ),
            else_ = (
                func.julianday(datetime.now()) -
                func.julianday(Job.accepted_timestamp)
            )*86400
        ).label('in_work'),
        case(
            (Job.success, 'success'),
            (Job.finished, 'failure'),
            (Job.accepted, 'in_work'),
            else_='waiting'
        ).label('status'),
        Job.progress,
        Job.error,
    )
    return query



def _query(session: Session, batch: str):
    query = _select()
    if batch is not None:
        query = query.filter(Job.batch == batch)
    query = query.order_by(Job.received_timestamp.desc())
    result = session.execute(query).all()
    return result

def _pretty_sec(seconds):
    if seconds is None:
        return "None"
    if np.isnan(seconds):
        return "None"
    seconds = int(seconds)
    if seconds<60:
        return f'{seconds}s'
    minutes = seconds//60
    seconds %= 60
    if minutes<60:
        return f'{minutes}m {seconds}s'
    hour = minutes//60
    minutes%=60
    return f'{hour}h {minutes}m {seconds}s'

def _to_html_lines(results):
    html = []
    batches = Query.en(results).feed(fluq.partition_by_selector(lambda z: z['batch'])).to_list()
    for batch in batches:
        first_line = True
        for result in batch:
            html.append('<tr>')
            html.append(f"<td>{result['id']}")
            if result['batch']!=result['id']:
                html.append(f'</br><span style="color:gray;">')
                html.append(result['batch'])
                html.append("</span>")
            html.append(f"<td>{result['decider']}</td>")
            html.append(f"<td>{result['received_timestamp']}")
            if result['in_queue'] is not None:
                html.append(f"<br/>Q: {_pretty_sec(result['in_queue'])}")
            if result['in_work'] is not None:
                html.append(f"<br/>W: {_pretty_sec(result['in_work'])}")
            html.append("</td>")
            html.append(f"<td>{result['status']}")
            if result['status'] == 'in_work':
                html.append(f"<br>T: {_pretty_sec((datetime.now()-result['accepted_timestamp']).total_seconds())}")
                if result['progress'] is not None:
                    html.append(f"<br> C: {int(100*result['progress'])}%")
            html.append("</td>")
            html.append("</tr>")

            if result['error'] is not None:
                html.append('<tr><td colspan=4><tt>')
                html.append(result['error'].replace('\n','<br>'))
                html.append('</tt></td></tr>')

    return '\n'.join(html)


def create_batch_page(session, batch):
    records = _query(session, batch)
    records = [r._asdict() for r in records]
    inner = _to_html_lines(records)
    return f'<html><body><table border=1>{inner}</table></body></html>'
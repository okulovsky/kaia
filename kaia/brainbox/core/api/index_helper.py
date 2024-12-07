from datetime import datetime

import numpy as np

from ..small_classes import BrainBoxJob
from sqlalchemy.orm import Session
from sqlalchemy import select, case, func
from yo_fluq_ds import *

def _calculate_julian_date(dt: datetime):
    julian_date = dt.toordinal() + 1721425.5
    return julian_date

def _select():
    query = select(
        BrainBoxJob.id,
        BrainBoxJob.batch,
        case((
            BrainBoxJob.method.isnot(None),
            BrainBoxJob.decider + ':' + BrainBoxJob.method),
            else_=BrainBoxJob.decider
        ).label("decider"),
        BrainBoxJob.received_timestamp,
        BrainBoxJob.accepted_timestamp,
        BrainBoxJob.finished_timestamp,
        (
                (func.julianday(BrainBoxJob.accepted_timestamp) -
                 func.julianday(BrainBoxJob.received_timestamp)
                 ) * 86400
        ).label('in_queue'),
        case(
            (
                BrainBoxJob.finished,
                (
                        func.julianday(BrainBoxJob.finished_timestamp) -
                        func.julianday(BrainBoxJob.accepted_timestamp)
                ) * 86400,
            ),
            else_ = (
                func.julianday(datetime.now()) -
                func.julianday(BrainBoxJob.accepted_timestamp)
            )*86400
        ).label('in_work'),
        case(
            (BrainBoxJob.success, 'success'),
            (BrainBoxJob.finished, 'failure'),
            (BrainBoxJob.accepted, 'in_work'),
            else_='waiting'
        ).label('status'),
        BrainBoxJob.progress,
        BrainBoxJob.error,
    )
    return query



def _query(session: Session, batch: str):
    query = _select()
    if batch is not None:
        query = query.filter(BrainBoxJob.batch == batch)
    query = query.order_by(BrainBoxJob.received_timestamp.desc())
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


def build_report(session, batch):
    records = _query(session, batch)
    records = [r._asdict() for r in records]
    inner = _to_html_lines(records)
    return f'<html><body><table border=1>{inner}</table></body></html>'
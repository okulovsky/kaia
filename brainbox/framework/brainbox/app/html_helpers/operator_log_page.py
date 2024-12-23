from ....job_processing import OperatorLogItem

def create_operator_log_page(log: list[OperatorLogItem]):
    html = []
    for item in log:
        html.append('<tr>')
        html.append(f'<td>{item.timestamp}</td>')
        html.append(f'<td>{item.level.name}</td>')
        html.append(f'<td>{item.id}</td>')
        html.append(f'<td>{item.event}</td>')
        if item.error is not None:
            error = item.error.replace('\n','<br>')
            html.append(f'<td><tt>{error}</tt></td>')
        html.append('</tr>')
    return '<html><body><table border=1 cellspacing=1>'+'\n'.join(html)+'</table></body></html>'


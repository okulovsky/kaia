from ..interface import InstallationReport
from ....common import HTML


def create_installation_report_page(report: InstallationReport):
    log = report.log
    html = ['<tt>']
    for item in log.items:
        line = f'[{str(item.timestamp):<15}]  {item.data}'
        html.append(line)
        html.append('<br>')
    return ''.join(html)
from .page import page
from ..interface import InstallationReport


def create_installation_report_page(report: InstallationReport):
    log = report.log
    html = ['<table>']
    for item in log.items:
        html.append('<tr valign=top>')
        html.append(f'<td>{item.timestamp}</td>')
        html.append('<td>')
        if item.comment is not None:
            html.append(item.comment)
        elif item.command is not None:
            html.append(" ".join(item.command.command))
        html.append('</td>')
        html.append('</tr>')
        if item.result is not None:
            html.append('<tr valign=top><td>&nbsp;</td><td>')
            html.append(item.result)
            html.append('</tr>')
    html.append('</table>')
    if report.error is not None:
        html.append("<h1>Exception</h1>")
        html.append("<tt>")
        html.append(report.error.replace(" ", "&nbsp").replace("\n", "<br>"))
        html.append("</tt>")
    return ''.join(html)
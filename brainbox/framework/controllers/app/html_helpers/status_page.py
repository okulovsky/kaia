import json

from ..interface import ControllerServiceStatus
from .page import page, button



def create_status_page(status: ControllerServiceStatus):
    html = []
    if status.currently_installing_container is not None:
        html.append(f'<a href="/html/controllers/installation_report">Installing {status.currently_installing_container}</a>')
    html.append('''
    <table cellspacing="0" border="1">
    <tr>
    <td>Name</td>
    <td>Installed/Size</td>
    <td>Installation commands</td>
    <td>Instances</td>
    <td>Run</td>
    <td>Self-test report</td>
    </tr>
    ''')
    for row in status.containers:
        html.append('<tr>')
        html.append(f'<td>{row.name}</td>')
        html.append(f'<td>{"☑" if row.installation_status.installed else "☐"} {str(row.installation_status.size)}</td>')

        if row.installation_status.dockerless_controller:
            html.append('<td>&nbsp;</td>'*4+'</tr>')
            continue

        html.append(f'<td>')
        html.append('<table border="0"><tr>')
        html.append("<td>")
        html.append(button('/controllers/install', "Install", dict(decider=row.name, join=False)))
        html.append('</td><td>')
        html.append(button('/controllers/uninstall', "Uninstall", dict(decider=row.name), active=row.installation_status.installed))
        html.append('</td><td>')
        html.append(button('/controllers/uninstall', "Purge", dict(decider=row.name, purge=True), active=row.installation_status.installed))
        html.append('</td><td>')
        html.append(button('/controllers/self_test', "Self-test", dict(decider=row.name), active=row.installation_status.installed))
        html.append('</td>')
        html.append('</tr></table>')
        html.append('</td>')

        html.append('<td><table border="0">')
        for instance in row.instances:
            html.append("<tr>")
            html.append(f"<td>{instance.instance_id}</td>")
            html.append(f"<td>{instance.parameter}</td>")
            if instance.address is not None:
                html.append(f'<td><a href="http://{instance.address}" target="_blank">{instance.address}</a></td>')
            else:
                html.append('<td>&nbsp;</td>')
            html.append(f"<td>")
            html.append(button("/controllers/stop", "Stop", dict(decider=row.name, instance_id=instance.instance_id)))
            html.append(f"</td></tr>")
        html.append("</table></td>")

        html.append("<td>")
        parameter_name = 'parameter_'+row.name
        html.append(f'<input type="text" id="{parameter_name}"/>')
        html.append(button('/controllers/run', "Run", dict(decider=row.name), dict(parameter=parameter_name), active=row.installation_status.installed))
        html.append("</td>")

        html.append("<td>")
        if row.has_self_test_report:
            html.append(f"<a href=/html/controllers/self_test_report/{row.name}>Self-test report</a>")
            if row.has_errors_in_self_test_report:
                html.append(f'⚠')
            html.append(button('/controllers/delete_self_test', "Delete", dict(decider=row.name)))
        else:
            html.append("&nbsp;")
        html.append("</td>")

        html.append("</tr>")

    html.append('</table>')
    return page(html)
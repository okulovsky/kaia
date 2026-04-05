from ..marshalling_2 import Server, ServiceComponent, IComponent
import argparse
import subprocess
import sys

def run_brainbox_app(
        services: list,
        allow_notebooks: bool = True,
):
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notebook', action='store_true')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.notebook:
        if allow_notebooks:
            print("Running notebook")
            subprocess.call(
                [sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip',
                 '0.0.0.0', "--NotebookApp.token=''"], cwd='/repo')
            exit(0)
        else:
            raise ValueError("Notebooks are not allowed for this container")

    print("Running server")
    components = []
    for index, service in enumerate(services):
        print(f"Mounting service {type(service).__name__} at index {index}")
        if isinstance(service, IComponent):
            components.append(service)
        else:
            component = ServiceComponent(service)
            components.append(component)

    print("Starting web-server")
    server = Server(8080, *components)
    server.create_web_app_entry_point().run()

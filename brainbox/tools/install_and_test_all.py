import traceback

from brainbox.framework import ControllerApi

def make(exclude=()):
    with ControllerApi.Test() as api:
        containers = api.status().containers
        containers = [c for c in containers if not c.installation_status.dockerless_controller]
        for c in containers:
            if c.name in exclude:
                continue
            stars = '*'*30
            print(f'\n\n{stars}\n{c.name}\n{stars}\n\n')
            if c.installation_status.installed:
                api.uninstall(c.name)
            api.delete_self_test(c.name)
            api.install(c.name)

            api.self_test(c.name)


if __name__ == '__main__':
    make('ComfyUI')
import traceback
from brainbox.framework import ControllerApi
from yo_fluq import Query

def make(exclude=(), include=(), start_with: str|None = None, install: bool = True, uninstall: bool = True):
    with ControllerApi.Test() as api:
        containers = api.status().containers
        containers = [c for c in containers if not c.installation_status.dockerless_controller]

        target_containers = containers
        if len(include) > 0:
            target_containers = [c for c in containers if c.name in include]
        if len(exclude) > 0:
            target_containers = [c for c in containers if c.name in exclude]
        if start_with is not None:
            target_containers = Query.en(target_containers).skip_while(lambda z: z.name!=start_with).to_list()


        for c in target_containers:
            stars = '*'*30
            print(f'\n\n{stars}\n{c.name}\n{stars}\n\n')
            api.delete_self_test(c.name)
            if uninstall and install:
                if c.installation_status.installed:
                    api.uninstall(c.name)
            if install:
                api.install(c.name)

            api.self_test(c.name)


if __name__ == '__main__':
    make()
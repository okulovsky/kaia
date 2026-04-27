import traceback
from brainbox.framework.app.controllers import ControllersApi
from yo_fluq import Query

def make(exclude=(), include=(), start_with: str|None = None, install: bool = True, uninstall: bool = True):
    with ControllersApi.test() as api:
        controllers = api.status().controllers
        controllers = [c for c in controllers if not c.dockerless]

        target_controllers = controllers
        if len(include) > 0:
            target_controllers = [c for c in controllers if c.name in include]
        if len(exclude) > 0:
            target_controllers = [c for c in controllers if c.name not in exclude]
        if start_with is not None:
            print([z.name for z in target_controllers])
            target_controllers = Query.en(target_controllers).skip_while(lambda z: z.name!=start_with).to_list()

        errors = {}

        for c in target_controllers:
            try:
                stars = '*'*30
                print(f'\n\n{stars}\n{c.name}\n{stars}\n\n')
                api.delete_self_test(c.name)
                if uninstall and install:
                    if c.installed:
                        api.uninstall(c.name)
                if install:
                    api.install(c.name)

                api.self_test(c.name)
            except Exception:
                errors[c.name] = traceback.format_exc()

        if len(errors) > 0:
            for key, error in errors.items():
                print("*"*40)
                print(key)
                print("*" * 40)
                print(error)
                print("\n\n\n")
            raise ValueError("Not all successfull: "+ " ".join(errors))



if __name__ == '__main__':
    make(
        uninstall=False
    )

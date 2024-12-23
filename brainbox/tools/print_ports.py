from brainbox.framework import ControllerRegistry

if __name__ == '__main__':
    registry = ControllerRegistry.discover()
    for name in registry.get_deciders_names():
        controller = registry.get_controller(name)
        settings = controller.get_default_settings()
        if hasattr(settings,'connection'):
            print(f'{name}\t\t{settings.connection.port}')
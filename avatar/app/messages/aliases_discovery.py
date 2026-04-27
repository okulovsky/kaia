from ...messaging import IMessage
import importlib
import pkgutil
import inspect


def create_aliases(namespaces: tuple[str,...]) -> dict[str, type]:
    all_subclasses = []
    for pkg in namespaces:
        all_subclasses.extend(_find_subclasses_in_package(IMessage, pkg))
    return {c.__name__: c for c in all_subclasses}


def _find_subclasses_in_package(base_class: type, package_name: str) -> list[type]:
    subclasses = []
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue  # Пропускаем модули, которые не удаётся импортировать
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, base_class) and obj is not base_class:
                subclasses.append(obj)
    return subclasses
import pickle

def try_pickle(obj, path='root'):
    try:
        pickle.dumps(obj)
        return None
    except Exception as e:
        return f"{path}: {e}"

def find_pickle_errors(obj, path='root', seen=None):
    if seen is None:
        seen = set()
    errors = []

    obj_id = id(obj)
    if obj_id in seen:
        return errors
    seen.add(obj_id)

    err = try_pickle(obj, path)
    if err is None:
        return errors  # объект сериализуется

    # Раскрываем составные объекты
    if isinstance(obj, dict):
        for k, v in obj.items():
            errors += find_pickle_errors(k, f"{path}.key({repr(k)})", seen)
            errors += find_pickle_errors(v, f"{path}[{repr(k)}]", seen)
    elif isinstance(obj, (list, tuple, set)):
        for i, item in enumerate(obj):
            errors += find_pickle_errors(item, f"{path}[{i}]", seen)
    elif hasattr(obj, '__dict__'):
        for attr_name, attr_value in vars(obj).items():
            errors += find_pickle_errors(attr_value, f"{path}.{attr_name}", seen)
    elif hasattr(obj, '__slots__'):
        for slot in obj.__slots__:
            try:
                attr_value = getattr(obj, slot)
                errors += find_pickle_errors(attr_value, f"{path}.{slot}", seen)
            except AttributeError:
                continue
    else:
        # Просто не сериализуемый примитив
        errors.append(f"{path}: {type(obj).__name__} is not picklable")

    return errors
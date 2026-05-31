def _find_id_by_title(js: dict, title: str) -> list[str]:
    results = []
    for key, value in js.items():
        if value['_meta']['title'] == title:
            results.append(key)
    return results


def _find_single_node_by_title(js: dict, title: str) -> dict:
    keys = _find_id_by_title(js, title)
    if len(keys) == 0:
        raise ValueError(f"Can't find the node with title {title}")
    if len(keys) > 1:
        raise ValueError(f"Too many nodes with title {title}")
    node = js[keys[0]]
    return node


def _find_ids_with_field(js: dict, field) -> list[str]:
    results = []
    for key, value in js.items():
        if field in value['inputs']:
            results.append(key)
    return results


def make_substitution(js: dict, field_name: str, value: object, node_title: str|None = None):
    if node_title is not None:
        node = _find_single_node_by_title(js, node_title)
        if field_name not in node['inputs']:
            raise ValueError(f'Field {field_name} not found in the node with title {node_title}')
    else:
        keys = _find_ids_with_field(js, field_name)
        if len(keys) == 0:
            raise ValueError(f"Can't find the node with field {field_name}")
        if len(keys) > 1:
            raise ValueError(f"Too many nodes with field {field_name}. Specify the title.")
        node = js[keys[0]]

    node['inputs'][field_name] = value
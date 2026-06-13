def normalize_values(values: list) -> list:
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        return list(values)
    return ['#NONE' if v is None else str(v) for v in values]


def normalize_selector_keys(d: dict) -> dict:
    keys = list(d.keys())
    normalized = normalize_values(keys)
    if keys == normalized:
        return d
    return dict(zip(normalized, d.values()))

from foundation_kaia.marshalling.documenter import ServiceDocumentation

_CSS = (
    'h2{border-bottom:2px solid #333;padding-bottom:.2em}'
    'h3{font-size:1em;margin:.8em 0 .2em}'
    '.ep{background:#f8f8f8;border:1px solid #ddd;border-radius:4px;padding:.8em 1em;margin-bottom:1em}'
    '.doc{color:#666;font-style:italic;margin:.3em 0}'
    '.t{color:#0066cc;font-family:monospace}'
    'ul{margin:.3em 0;padding-left:1.4em}'
    'li{margin:.15em 0}'
    'b{font-family:monospace}'
)


def build_snippet(docs: list[ServiceDocumentation]) -> str:
    parts = [f'<style>{_CSS}</style>']
    for svc in docs:
        parts.append(f'<h2>{svc.name}</h2>')
        if svc.docstring:
            parts.append(f'<p class="doc">{svc.docstring.strip()}</p>')
        for ep in svc.endpoints.values():
            parts.append(f'<div class="ep"><h3><code>{ep.url_template}</code></h3>')
            if ep.docstring:
                parts.append(f'<p class="doc">{ep.docstring.strip()}</p>')
            schema = ep.json_schema.to_dict()
            props = schema.get('properties', {})
            defs = schema.get('$defs', {})
            if props or ep.file_params:
                parts.append('<ul>')
                for name, prop in props.items():
                    parts.append(f'<li>{_schema_item(name, prop, defs)}</li>')
                for name in ep.file_params:
                    parts.append(f'<li><b>{name}</b>: <span class="t">file</span></li>')
                parts.append('</ul>')
            ret = ep.return_type + (' (file)' if ep.return_is_file else '')
            parts.append(f'<p><b>Returns:</b> <code>{ret}</code></p></div>')
    return ''.join(parts)


def _schema_item(name: str, schema: dict, defs: dict) -> str:
    type_str = _schema_type(schema, defs)
    children = _schema_children(schema, defs)
    label = f'<b>{name}</b>: <span class="t">{type_str}</span>'
    if children:
        return label + '<ul>' + ''.join(f'<li>{c}</li>' for c in children) + '</ul>'
    return label


def _schema_type(schema: dict, defs: dict) -> str:
    if '$ref' in schema:
        schema = _resolve_ref(schema['$ref'], defs)
    if 'anyOf' in schema:
        return ' | '.join(_schema_type(s, defs) for s in schema['anyOf'])
    t = schema.get('type')
    if t == 'array':
        items = schema.get('items', {})
        return f'array[{_schema_type(items, defs)}]'
    if t == 'object':
        return 'object'
    if isinstance(t, list):
        return ' | '.join(t)
    return t or 'any'


def _schema_children(schema: dict, defs: dict) -> list[str]:
    if '$ref' in schema:
        schema = _resolve_ref(schema['$ref'], defs)
    if 'anyOf' in schema:
        children = []
        for s in schema['anyOf']:
            children.extend(_schema_children(s, defs))
        return children
    t = schema.get('type')
    if t == 'object':
        return [_schema_item(n, p, defs) for n, p in schema.get('properties', {}).items()]
    if t == 'array':
        return _schema_children(schema.get('items', {}), defs)
    return []


def _resolve_ref(ref: str, defs: dict) -> dict:
    name = ref.split('/')[-1]
    return defs.get(name, {})

import base64, pickle
from .formatter import IFormatter, SerializationPath

class DefaultFormatter(IFormatter):
    def __init__(self):
        self.not_null = False

    def _to_json(self, value, path: SerializationPath):
        if isinstance(value, (str, float, int, bool)):
            return value
        if isinstance(value, list) or isinstance(value, tuple):
            return [self.to_json(v, path.append(i)) for i, v in enumerate(value)]
        if isinstance(value, dict):
            return {k: self.to_json(v, path.append(k)) for k, v in value.items()}
        return {
            '@base64': None,
            '@content': base64.b64encode(pickle.dumps(value)).decode('ascii')
        }

    def _from_json(self, value, path: SerializationPath):
        if isinstance(value, (str, float, int, bool)):
            return value
        if isinstance(value, list):
            return [self.from_json(v, path.append(i)) for i, v in enumerate(value)]
        if isinstance(value, dict):
            if '@base64' in value:
                return pickle.loads(base64.b64decode(value['@content']))
            return {k:self.from_json(v, path.append(k)) for k, v in value.items()}
        else:
            path.from_json.type(value, "primitive, list or dict")





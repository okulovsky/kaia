import json
import pickle
import base64



class NoTupleJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple):
            raise TypeError("Tuples are not allowed in JSON serialization.")
        return super().default(obj)


class Format:
    CONTROL_FIELD = '@type'
    CONTENT_FIELD = '@content'

    @staticmethod
    def check_json(obj):
        if obj is None:
            return True
        if isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, bool):
            return True
        if isinstance(obj, list):
            return all(Format.check_json(z) for z in obj)
        if isinstance(obj, dict):
            return all(Format.check_json(z) for z in obj.values())
        return False

    @staticmethod
    def encode(data: dict):
        result = {}
        for key, value in data.items():
            if Format.check_json(value):
                result[key] = value
            else:
                s = base64.b64encode(pickle.dumps(value)).decode('ascii')
                result[key] = {Format.CONTROL_FIELD: 'base64', Format.CONTENT_FIELD: s}
        return result

    @staticmethod
    def decode(data: dict):
        result = {}
        for key in data:
            if (
                isinstance(data[key], dict) and
                Format.CONTROL_FIELD in data[key] and
                Format.CONTENT_FIELD in data[key]
            ):
                if data[key][Format.CONTROL_FIELD] == 'base64':
                    result[key] =  pickle.loads(base64.b64decode(data[key][Format.CONTENT_FIELD]))
                else:
                    raise ValueError("only @type=base64 is supported")
            else:
                result[key] = data[key]
        return result

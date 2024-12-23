from .marshalling_metadata import MarshallingMetadata
from .format import Format
import flask
import traceback


class ServerBinding:
    def __init__(self,
                 meta :MarshallingMetadata,
                 custom_method_name: str|None = None
                 ):
        self.meta = meta
        self.custom_method_name = custom_method_name

    @property
    def __name__(self):
        if self.custom_method_name is None:
            return self.meta.name
        return self.custom_method_name

    def _get_arguments(self, kwargs, arguments):
        arguments = Format.decode(arguments)
        for key, value in kwargs.items():
            if key in arguments:
                raise ValueError(f"{key} is provided via address and via json")
            arguments[key] = value
        return arguments

    def _process(self, kwargs, arguments):
        arguments = self._get_arguments(kwargs, arguments)
        result = self.meta.method(**arguments)
        result = dict(result=result, error = None)
        result = Format.encode(result)
        return result

    def __call__(self, **kwargs):
        arguments = flask.request.json
        try:
            return flask.jsonify(self._process(kwargs, arguments))
        except:
            return flask.jsonify(dict(result=None, error=traceback.format_exc())), 500









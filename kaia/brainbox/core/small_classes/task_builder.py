from typing import Type
from .task import BrainBoxTask
from .arguments_validator import ArgumentsValidator

class BrainBoxTaskBuilderResult:
    def __init__(self, type, method, arguments):
        self.id = BrainBoxTask.safe_id()
        self.type = type
        self.method = method
        self.arguments = arguments

    def to_task(self,
                decider_parameters: None | str = None,
                id: None|str = None,
                dependencies: None|dict[str,str] = None
                ) -> BrainBoxTask:
        return BrainBoxTask(
            decider=getattr(self.type, self.method) if self.method is not None else self.type,
            arguments=self.arguments,
            decider_parameters=decider_parameters,
            id = self.id if id is None else id,
            dependencies=dependencies
        )


class BrainBoxTaskBuilder:
    def __init__(self, type: Type, method:str | None = None):
        self._type = type
        self._method = method
        self._arguments = None

    def _assign_args(self, args) -> dict:
        method = self._method
        if method is None:
            method = '__call__'
        method_instance = getattr(self._type, method)
        validator = ArgumentsValidator.from_signature(method_instance)
        if len(validator.arguments_sequence) < len(args):
            raise ValueError(f"Too much arguments: method defines {validator.arguments_sequence}, arguments are {args}")
        result = {}
        for i, v in enumerate(args):
            result[validator.arguments_sequence[i]] = v
        return result


    def __call__(self, *args, **kwargs):
        dct = {}
        if len(args) > 0:
            dct = self._assign_args(args)
        for key, value in kwargs.items():
            if key in dct:
                raise ValueError(f'Duplicate argument {key} (new value is {value}, existing value is {dct[key]}')
            dct[key] = value
        return BrainBoxTaskBuilderResult(self._type, self._method, dct)


    def __getattr__(self, item):
        return BrainBoxTaskBuilder(self._type, item)


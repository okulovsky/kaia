from ...common import SignatureProcessor
from ..app import IBrainBoxTask
from .one_brainbox_task_factory import IOneBrainBoxTaskFactory
from ...common import IDecider



class BrainBoxTaskBuilderResult(IOneBrainBoxTaskFactory):
    def __init__(self,
                 type: type,
                 method:str | None = None,
                 arguments: dict|None = None,
                 ordering_token: str|None = None,
                 fake_dependencies: list[str|IBrainBoxTask]|None = None,
                 decider_parameter: str|None = None,
                 ):
        self._type = type
        self._method = method
        self._arguments: dict|None = arguments
        self._ordering_token = ordering_token
        self._fake_dependencies = fake_dependencies
        self._id = IBrainBoxTask.safe_id()
        self._decider_parameter = decider_parameter


    def to_task(self, id: str|None = None, batch_id: str|None = None) -> IBrainBoxTask:
        from .task import BrainBoxTask
        actual_id = id if id is not None else self._id

        return BrainBoxTask(
            id = actual_id,
            decider = self._type,
            decider_method = self._method,
            arguments=self._arguments,
            decider_parameter=self._decider_parameter,
            ordering_token=self._ordering_token,
            fake_dependencies=self._fake_dependencies,
            batch=batch_id if batch_id is not None else actual_id
        )




    def dependent_on(self, *args: str|IBrainBoxTask):
        return BrainBoxTaskBuilderResult(self._type, self._method, self._arguments, self._ordering_token, list(args))


def _get_ordering_token(tp: type[IDecider], arguments: dict):
    ordering_sequence = tp.get_ordering_arguments_sequence()
    if ordering_sequence is None:
        return None
    ordering_sequence = {argname: index for index, argname in enumerate(ordering_sequence)}
    ordering_parts = {}
    for key, value in arguments.items():
        if key in ordering_sequence:
            ordering_parts[ordering_sequence[key]] = str(value)
    for idx in ordering_sequence.values():
        if idx not in ordering_parts:
            ordering_parts[idx] = '*'
    ordering_token = '/'.join(ordering_parts[k] for k in sorted(ordering_parts))
    return ordering_token



class BrainBoxTaskBuilder:
    def __init__(self,
                 _type: type[IDecider],
                 method: str|None = None,
                 parameter: str|None = None,
                 ):
        self._type = _type
        self._method = method
        self._decider_parameter = parameter



    def __call__(self, *args, **kwargs) -> BrainBoxTaskBuilderResult:
        method = self._method
        if method is None:
            method = '__call__'
        method_instance = getattr(self._type, method)
        validator = SignatureProcessor.from_signature(method_instance)
        arguments = validator.to_kwargs_only(*args, **kwargs)
        return BrainBoxTaskBuilderResult(
            self._type,
            self._method,
            arguments,
            _get_ordering_token(self._type, arguments),
            decider_parameter = self._decider_parameter
        )


    def __getattr__(self, method) -> 'BrainBoxTaskBuilder':
        if not hasattr(self._type, method) or not callable(getattr(self._type, method)):
            raise ValueError(f"Type {self._type} doesn't contain method {method}")
        return BrainBoxTaskBuilder(self._type, method, self._decider_parameter)




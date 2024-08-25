from .task import BrainBoxTask

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
    def __init__(self, type, method = None):
        self._type = type
        self._method = method
        self._arguments = None

    def __call__(self, *args, **kwargs):
        if len(args) > 0:
            raise ValueError("Not yet implemented")
        return BrainBoxTaskBuilderResult(self._type, self._method, kwargs)

    def __getattr__(self, item):
        return BrainBoxTaskBuilder(self._type, item)


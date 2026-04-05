from dataclasses import dataclass

from docutils.nodes import title

from foundation_kaia.marshalling_2 import Serializer, EndpointDocumentation, JsonSchema
from ...common.decider_model import DeciderModel, DeciderMethodModel
from ...controllers import IController, ControllerOverDecider
from ...task import JobRequest

@dataclass
class SelfTestCaseDocumentation:
    title: str | None
    method: str
    arguments: dict


@dataclass
class DeciderMethodDocumentation:
    method_name: str
    docstring: str | None
    endpoint: EndpointDocumentation | None
    arguments: JsonSchema
    self_test_cases: list[SelfTestCaseDocumentation]
    is_file: list[str]
    result_is_file: bool

    @staticmethod
    def parse(decider_method: DeciderMethodModel, self_test_cases: list, is_marshalling_api: bool) -> 'DeciderMethodDocumentation':
        ep = decider_method.endpoint
        method_name = decider_method.method_name

        endpoint_doc = EndpointDocumentation.parse(ep) if is_marshalling_api else None

        arguments = JsonSchema.from_fields({
            arg.name: Serializer(arg.annotation).to_json_schema()
            for arg in ep.signature.arguments
        })

        method_cases = []
        for case in self_test_cases:
            job_request: JobRequest = case.task.to_job_request()
            if len(job_request.jobs) != 1:
                raise ValueError("Each task in self-test must produce exactly one job")
            job_description = job_request.jobs[0]
            if job_description.method != method_name:
                continue
            method_cases.append(SelfTestCaseDocumentation(
                title = case.title,
                method=method_name,
                arguments = job_description.arguments
            ))

        return DeciderMethodDocumentation(
            method_name=method_name,
            docstring=ep.signature.callable.__doc__,
            endpoint=endpoint_doc,
            arguments=arguments,
            self_test_cases=method_cases,
            is_file=list(decider_method.file_argument_names),
            result_is_file=decider_method.result_is_file,
        )


@dataclass
class DeciderDocumentation:
    name: str
    docstring: str | None
    methods: list[DeciderMethodDocumentation]

    @staticmethod
    def parse(name: str, api_class, controller: IController) -> 'DeciderDocumentation':
        if api_class is None:
            return DeciderDocumentation(name=name, docstring=None, methods=[])

        is_marshalling_api = not isinstance(controller, ControllerOverDecider)
        self_test_cases = list(controller.self_test_cases())
        decider_model = DeciderModel.parse(api_class)

        methods = [
            DeciderMethodDocumentation.parse(dm, self_test_cases, is_marshalling_api)
            for dm in decider_model.methods.values()
        ]

        return DeciderDocumentation(
            name=name,
            docstring=api_class.__doc__,
            methods=methods,
        )

from dataclasses import dataclass
from foundation_kaia.marshalling_2 import EndpointModel, ServiceModel, ResultType, DeclaredType
from foundation_kaia.marshalling_2.marshalling.model.service_model import _SERVICE_ATTR


@dataclass
class DeciderMethodModel:
    method_name: str
    endpoint: EndpointModel
    file_argument_names: frozenset[str]
    result_is_file: bool

    @staticmethod
    def from_endpoint(ep: EndpointModel) -> 'DeciderMethodModel':
        file_names = [p.name for p in ep.params.file_params]
        if ep.params.binary_stream_param is not None:
            file_names.append(ep.params.binary_stream_param.name)

        result_is_file = ep.result.type in (
            ResultType.BinaryFile,
            ResultType.StringIterable,
            ResultType.CustomIterable,
        )

        return DeciderMethodModel(
            method_name=ep.signature.name,
            endpoint=ep,
            file_argument_names=frozenset(file_names),
            result_is_file=result_is_file,
        )


@dataclass
class DeciderModel:
    methods: dict[str, DeciderMethodModel]
    services: tuple[ServiceModel, ...]

    @staticmethod
    def parse(api_class) -> 'DeciderModel':
        dt = DeclaredType.parse(api_class)
        services: list[ServiceModel] = []
        methods: dict[str, DeciderMethodModel] = {}
        seen_methods: set[str] = set()

        for mro_elem in dt.mro:
            if _SERVICE_ATTR not in mro_elem.type.__dict__:
                continue
            tp = mro_elem.generic_type or mro_elem.type
            service = ServiceModel.parse(tp)
            services.append(service)
            for ep in service.endpoints:
                method_name = ep.signature.name
                if method_name not in seen_methods:
                    seen_methods.add(method_name)
                    methods[method_name] = DeciderMethodModel.from_endpoint(ep)

        return DeciderModel(methods=methods, services=tuple(services))

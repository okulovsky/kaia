from dataclasses import dataclass
from ..protocol import EndpointModel, ResultType
from ..reflector import Annotation
from ..serialization import Serializer
from ..serialization.json_schema import JsonSchema


def _annotation_to_str(annotation: Annotation) -> str:
    return '|'.join(z.self.type.__name__ for z in annotation.types)


@dataclass
class EndpointDocumentation:
    name: str
    docstring: str | None
    url_template: str          # e.g. /tasks/get-job/<id>?optional=<optional>
    json_schema: JsonSchema    # JSON Schema object for the JSON body params
    file_params: list[str]     # names of file/stream params
    return_type: str
    return_is_file: bool

    @staticmethod
    def parse(ep: EndpointModel) -> 'EndpointDocumentation':
        parts = [ep.endpoint_address]
        for p in ep.params.path_params:
            parts.append(f'<{p.name}>')
        if ep.params.pathlike_param is not None:
            parts.append(f'<{ep.params.pathlike_param.name}>')
        url = '/' + '/'.join(parts)
        query_parts = [f'{p.name}=<{p.name}>' for p in ep.params.query_params]
        if query_parts:
            url += '?' + '&'.join(query_parts)

        json_schema = JsonSchema.from_fields({
            p.name: Serializer(p.argument_description.annotation).to_json_schema()
            for p in ep.params.json_params
        })

        file_params = [arg.name for arg in ep.params.file_params]
        if ep.params.binary_stream_param is not None:
            file_params.append(ep.params.binary_stream_param.name)
        if ep.params.custom_stream_param is not None:
            file_params.append(ep.params.custom_stream_param.argument_description.name)

        return_is_file = ep.result.type == ResultType.BinaryFile

        return EndpointDocumentation(
            name=ep.signature.name,
            docstring=ep.signature.callable.__doc__,
            url_template=url,
            json_schema=json_schema,
            file_params=file_params,
            return_type=_annotation_to_str(ep.signature.returned_type),
            return_is_file=return_is_file,
        )

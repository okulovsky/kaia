from urllib.parse import urlparse
from starlette.datastructures import QueryParams
from starlette.routing import compile_path
from foundation_kaia.marshalling import EndpointModel, CallModel, parse_url, build_route_path


def _decompose_url(url: str, model: EndpointModel) -> tuple[dict, dict]:
    parsed = urlparse(url)

    route_path = build_route_path(model)
    path_regex, _, _ = compile_path(route_path)
    match = path_regex.match(parsed.path)
    if match is None:
        raise ValueError(
            f"URL path '{parsed.path}' does not match route '{route_path}': "
            f"expected {len(model.params.path_params)} path parameter(s)"
        )
    path_params = match.groupdict()

    query_params = QueryParams(parsed.query)
    return path_params, query_params



def make_url_test(f, *args, **kwargs):
    call_model = CallModel.Factory.test(f)(*args, **kwargs)
    model = call_model.endpoint_model
    url = call_model.content.url
    path_params, query_params = _decompose_url(url, model)
    parsed_kwargs = {}
    parse_url(parsed_kwargs, model, path_params, query_params)
    return call_model.content, parsed_kwargs

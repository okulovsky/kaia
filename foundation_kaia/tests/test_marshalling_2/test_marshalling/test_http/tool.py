from foundation_kaia.marshalling_2.marshalling.model import CallModel
from foundation_kaia.marshalling_2.marshalling.http_protocol.content_producer import ContentProducer
from foundation_kaia.marshalling_2.marshalling.http_protocol.parse_content import parse_content


def make_content_test(f, *args):
    call_model = CallModel.Factory.test(f)(*args)
    content = call_model.content
    model = call_model.endpoint_model
    producer = ContentProducer(content)
    body = list(producer.produce())
    kwargs = {}
    parse_content(kwargs, producer.content_type, body, model)
    return content, kwargs

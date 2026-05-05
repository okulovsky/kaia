from foundation_kaia.marshalling import CallModel, ContentProducer, parse_content

def make_content_test(f, *args):
    call_model = CallModel.Factory.test(f)(*args)
    content = call_model.content
    model = call_model.endpoint_model
    producer = ContentProducer(content, model)
    body = list(producer.produce())
    kwargs = {}
    parse_content(kwargs, body, model, producer.content_type)
    return content, kwargs

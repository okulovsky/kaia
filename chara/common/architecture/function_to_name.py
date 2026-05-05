from foundation_kaia.marshalling import Signature, FunctionKind

def function_to_name(f):
    if not callable(f):
        raise ValueError(f"{f} was not callable")
    try:
        signature = Signature.parse(f)
        if signature.kind == FunctionKind.FUNCTION:
            return signature.name
        elif signature.kind == FunctionKind.LAMBDA:
            return 'lambda'
        else:
            qualname = f.__qualname__
            class_name = qualname.rsplit('.', 1)[0]
            return class_name + "-" + signature.name
    except TypeError:
        if hasattr(f, '__call__'):
            return type(f).__name__
        raise ValueError("Unknown type of the function")



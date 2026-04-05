from foundation_kaia.marshalling_2 import service, endpoint
from .decider_documentation import DeciderDocumentation


@service
class IDeciderService:
    @endpoint(method='GET')
    def decider_doc(self, name: str) -> DeciderDocumentation:
        ...

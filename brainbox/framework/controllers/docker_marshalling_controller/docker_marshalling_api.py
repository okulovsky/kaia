from ..docker_web_service_controller import DockerWebServiceApi, TController
from foundation_kaia.marshalling import ApiCall
from .docker_marshalling_endpoint import DockerMarshallingApiCall
from brainbox.framework.common.decider_model import DeciderModel
from typing import Generic
from ..architecture import TSettings


class DockerMarshallingApi(DockerWebServiceApi[TSettings, TController], Generic[TSettings, TController]):
    def __init__(self, address: str|None):
        super().__init__(address)
        decider_model = DeciderModel.parse(type(self))
        for name, decider_method in decider_model.methods.items():
            call = ApiCall('', decider_method.endpoint)
            setattr(self, name, DockerMarshallingApiCall(self, call, decider_method))


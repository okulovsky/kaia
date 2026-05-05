from ..docker_web_service_controller import DockerWebServiceApi, TController
from foundation_kaia.marshalling import ApiCall, ApiUtils
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

    def wait_for_connection(self, timeout_in_seconds: int = 10):
        ApiUtils.wait_for_reply(self.base_url, timeout_in_seconds)



from dataclasses import dataclass
from .endpoint_model import EndpointModel
from typing import Any

@dataclass
class EndpointRegistrationData:
    endpoint: EndpointModel
    service: Any
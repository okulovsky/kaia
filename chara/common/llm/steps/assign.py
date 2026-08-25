from .step import LLMRequestStep
from foundation_kaia.prompters import AddressLike

class Assign(LLMRequestStep):
    def __init__(self, address: AddressLike):
        self.address = address

    def get_assignment_address(self) -> AddressLike|None:
        return self.address

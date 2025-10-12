from abc import abstractmethod, ABC
from .build_context import BuildContext

class IBuilderPart(ABC):
    @abstractmethod
    def to_commands(self, context: BuildContext) -> list[str]:
        pass
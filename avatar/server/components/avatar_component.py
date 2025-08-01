from abc import ABC, abstractmethod
import flask

class IAvatarComponent(ABC):
    @abstractmethod
    def setup_server(self, app: flask.Flask):
        pass
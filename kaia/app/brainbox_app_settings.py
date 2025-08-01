from dataclasses import dataclass
from .app import KaiaApp, IAppInitializer

@dataclass
class BrainboxAppSettings(IAppInitializer):
    def bind_app(self, app: 'KaiaApp'):
        pass

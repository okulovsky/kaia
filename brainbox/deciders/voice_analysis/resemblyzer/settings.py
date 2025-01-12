from dataclasses import dataclass
from brainbox.framework import ConnectionSettings

@dataclass
class ResemblyzerSettings:
    connection: ConnectionSettings = ConnectionSettings(20103)

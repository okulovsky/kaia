from dataclasses import dataclass

@dataclass
class OpenTTSSettings:
    image_name: str = 'synesthesiam/opentts:en'
    port: int = 11002
    name: str = 'opentts'
    address: str = '127.0.0.1'
    waiting_time: int = 30
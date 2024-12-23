from dataclasses import dataclass
from ....framework import ConnectionSettings

class OllamaModel:
    def __init__(self, name: str, location: str|None = None):
        self.name = name
        if location is None:
            location = name
            if '/' not in location:
                location='library/'+location
            if ':' in location:
                location = location.replace(':','/')
            else:
                location = location+'/latest'
        self.location = location

@dataclass
class OllamaSettings:
    connection = ConnectionSettings(20401, 10)
    models_to_install: tuple[OllamaModel,...] = (
        OllamaModel('llama3.2:1b'),
    )

from dataclasses import dataclass

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
    port: int = 11012
    startup_time_in_seconds: int = 30
    models_to_install: tuple[OllamaModel,...] = (
        OllamaModel('llama3.2:1b'),
    )

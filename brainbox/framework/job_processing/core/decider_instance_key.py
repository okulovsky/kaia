from dataclasses import dataclass

@dataclass
class DeciderInstanceKey:
    decider_name: str
    parameter: str|None
    def __str__(self):
        return f'{self.decider_name}/{self.parameter}'
    def __hash__(self):
        return self.__str__().__hash__()

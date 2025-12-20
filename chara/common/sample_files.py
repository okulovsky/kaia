from pathlib import Path

class SamplesClass:
    def __init__(self):
        self.root = Path(__file__).parent/'files'

    @property
    def lina(self):
        return self.root/'voice/'


Samples = SamplesClass()
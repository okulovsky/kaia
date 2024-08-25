import json
from kaia.brainbox.core import IDecider, File
from io import StringIO

class FakeLLMDecider(IDecider):
    def __init__(self):
        self.fake_model = None
        pass

    def warmup(self, parameters: str):
        self.fake_model = parameters


    def cooldown(self, parameters: str):
        self.fake_model = None


    def __call__(self, prompt: str):
        return f"LLM result for: {prompt}"
from ...core import IDecider

class FakeDubDecider(IDecider):
    def warmup(self):
        pass

    def cooldown(self):
        pass

    def dub(self, voice: str, text: str):
        return [text, text.upper()]
from .language import Language
from brainbox import IDecider
from brainbox.deciders import Zonos, EspeakPhonemizer

class LanguageToDecider:
    @staticmethod
    def map(language: Language|str, decider: type[IDecider]):
        if isinstance(language, Language):
            language = language.name
        if language == 'en' and (decider == Zonos or decider == EspeakPhonemizer):
            return 'en-us'
        return language

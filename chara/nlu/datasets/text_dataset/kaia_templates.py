from grammatron import Template

MOODS = (
    'User speaks neutrally and clearly',
    'User speaks quickly and briefly, no filler words',
    "User is angry because of the previous unsuccessful attempts, speaks accordingly",
    "User is in a good mood and speaks with assistant as if it was a real person",
)

LANGUAGES = ('en', 'de', 'ru')


def kaia_intent_templates() -> list[Template]:
    """The intents of the Kaia assistant: the templates the text dataset paraphrases"""
    from kaia.app import AssistantFactory
    assistant = AssistantFactory(None).create_assistant(None)
    templates = []
    for pack in assistant.get_intents():
        templates.extend(pack.templates)
    return templates

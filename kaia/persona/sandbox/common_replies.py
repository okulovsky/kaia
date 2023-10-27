from ..dub.languages import en
from ..dub.core import TemplatesCollection

class CommonReplies(TemplatesCollection):
    not_recognized = en.Template(
        "I don't understand!"
    )

    wrong_input = en.Template(
        "It does not make sense!"
    )

    wrong_state = en.Template(
        "I'm confused."
    )
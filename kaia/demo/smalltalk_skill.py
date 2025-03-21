from kaia.dub.languages.en import *

class SmalltalkInputs(TemplatesCollection):
    you_are_awesome = Template("You are awesome!")


class SmalltalkReply(TemplatesCollection):
    thanks_you_too = Template("Aw, thanks! You too!").meta.set(reply_to=SmalltalkInputs.you_are_awesome)


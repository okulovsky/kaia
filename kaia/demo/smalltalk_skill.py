from eaglesong.templates import *

class SmalltalkInputs(TemplatesCollection):
    you_are_awesome = Template("You are awesome!")


class SmalltalkReply(TemplatesCollection):
    thanks_you_too = Template("Aw, thanks! You too!").context(reply_to=SmalltalkInputs.you_are_awesome)


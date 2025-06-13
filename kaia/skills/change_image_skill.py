from typing import *
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext, Message
from avatar import World
from brainbox import File
from eaglesong import ContextRequest

class ChangeImageIntents(TemplatesCollection):
    change_image = Template("Change image")
    bad_image = Template("Bad image")
    hide_image = Template("Hide image")
    good_image = Template('Good image')
    describe_image = Template("Describe image", "Show prompt")

class ChangeImageReplies(TemplatesCollection):
    thanks = (
        Template("Thanks, I'm flattered! You're cute too!")
        .context(
            f'{World.user} sees {World.character} and says that {World.character} looks good',
            reply_to=ChangeImageIntents.good_image
        )
    )

class ChangeImageSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(ChangeImageIntents, ChangeImageReplies)
        self.last_image: Optional[File] = None



    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        avatar_api = context.avatar_api
        if input in ChangeImageIntents.change_image:
            yield avatar_api.image_get_new()
        elif input in ChangeImageIntents.bad_image:
            avatar_api.image_report('bad')
            yield avatar_api.image_get_new()
        elif input in ChangeImageIntents.hide_image:
            yield avatar_api.image_get_empty()
        if input in ChangeImageIntents.good_image:
            avatar_api.image_report('good')
            yield ChangeImageReplies.thanks.utter()
        if input in ChangeImageIntents.describe_image:
            desc = avatar_api.image_get_current_description()
            if desc is not None:
                yield Message(Message.Type.System, desc)





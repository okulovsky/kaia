from typing import *
from kaia.dub.languages.en import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext, Message
from kaia.avatar import World
from brainbox import File
from eaglesong import ContextRequest

class ChangeImageIntents(TemplatesCollection):
    change_image = Template("Change image")
    bad_image = Template("Bad image")
    hide_image = Template("Hide image")
    good_image = Template('Good image')
    describe_image = Template(
        "Describe image",
        "Show prompt"
    )

class ChangeImageReplies(TemplatesCollection):
    thanks = (
        Template("Thanks, I'm flattered! You're cute too!")
        .paraphrase(f'{World.user} sees {World.character} and says that {World.character} looks good')
    )

class ChangeImageSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(ChangeImageIntents, ChangeImageReplies)
        self.last_image: Optional[File] = None



    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        avatar_api = context.avatar_api
        if input.template.name == ChangeImageIntents.change_image.name:
            yield avatar_api.image_get_new()
        elif input.template.name == ChangeImageIntents.bad_image.name:
            avatar_api.image_report('bad')
            yield avatar_api.image_get_new()
        elif input.template.name == ChangeImageIntents.hide_image.name:
            yield avatar_api.image_get_empty()
        if input.template.name == ChangeImageIntents.good_image.name:
            avatar_api.image_report('good')
            yield ChangeImageReplies.thanks.utter()
        if input in ChangeImageIntents.describe_image:
            desc = avatar_api.image_get_current_description()
            if desc is not None:
                yield Message(Message.Type.System, desc)





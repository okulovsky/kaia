from typing import *
from kaia.eaglesong.core import Image
from kaia.avatar.dub.languages.en import *
from kaia.kaia.core import SingleLineKaiaSkill
from kaia.avatar.server import AvatarAPI


class ChangeImageIntents(TemplatesCollection):
    change_image = Template("Change image")
    bad_image = Template("Bad image")
    hide_image = Template("Hide image")

class ChangeImageReplies(TemplatesCollection):
    answer = Template("Here is a new image for you")





class ChangeImageSkill(SingleLineKaiaSkill):
    def __init__(self, avatar_api: AvatarAPI):
        super().__init__(ChangeImageIntents, ChangeImageReplies)
        self.avatar_api = avatar_api
        self.last_image: Optional[Image] = None



    def run(self):
        input: Utterance = yield
        if input.template.name == ChangeImageIntents.change_image.name:
            self.last_image = self.avatar_api.image_get()
            yield self.last_image
        if input.template.name == ChangeImageIntents.bad_image.name:
            if self.last_image is not None:
                self.avatar_api.image_report(self.last_image.id)
            self.last_image = self.avatar_api.image_get()
            yield self.last_image
        if input.template.name == ChangeImageIntents.hide_image.name:
            yield self.avatar_api.empty_image()




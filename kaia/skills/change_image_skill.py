from grammatron import *
from kaia import SingleLineKaiaSkill, ImageService, World

class ChangeImageIntents(TemplatesCollection):
    change_image = Template("Change image")
    bad_image = Template("Bad image")
    hide_image = Template("Hide image")
    good_image = Template('Good image')
    restore_image = Template("Restore image")
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

    def run(self):
        input: Utterance = yield
        if input in ChangeImageIntents.change_image:
            yield ImageService.NewImageCommand()
        elif input in ChangeImageIntents.bad_image:
            yield ImageService.ImageFeedback("bad")
            yield ImageService.NewImageCommand()
        elif input in ChangeImageIntents.hide_image:
            yield ImageService.HideImageCommand()
        elif input in ChangeImageIntents.restore_image:
            yield ImageService.RestoreImageCommand()
        if input in ChangeImageIntents.good_image:
            yield ImageService.ImageFeedback("good")
            yield ChangeImageReplies.thanks.utter()
        if input in ChangeImageIntents.describe_image:
            yield ImageService.ImageDescriptionCommand()





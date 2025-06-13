import random
from typing import *
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from avatar import World, WorldFields
from eaglesong import ContextRequest

ACTIVITY = TemplateVariable("activity", description=f"Activity {World.character} can be doing")

class ActivityIntents(TemplatesCollection):
    change_activity = Template("Change activity", "Do something else")
    activity_request = Template("What are you doing?")

class ActivityReplies(TemplatesCollection):
    current_activity = (
        Template(f"I'm {ACTIVITY}")
        .context(
            f"{World.user} asks {World.character} of what {World.character.pronoun} is doing, and {World.character} replies",
            reply_to=ActivityIntents.activity_request
        )
    )

    activity_changed = (
        Template(f"Sure. I'll be busy {ACTIVITY}")
        .context(
            f"{World.character} changes the activity and says what {World.character.pronoun} is doing.",
            reply_to=ActivityIntents.change_activity
        )
    )





class ActivitySkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(ActivityIntents, ActivityReplies)

    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        if input in ActivityIntents.change_activity:
            yield from context.avatar_api.narration_randomize_activity()
            activity = context.avatar_api.state_get().get(WorldFields.activity, None)
            if activity is not None:
                yield ActivityReplies.activity_changed(activity)
        if input in ActivityIntents.activity_request:
            activity = context.avatar_api.state_get().get(WorldFields.activity, None)
            if activity is not None:
                yield ActivityReplies.current_activity(activity)












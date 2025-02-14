import random
from typing import *
from kaia.dub.languages.en import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from kaia.avatar import World, KnownFields
from eaglesong import ContextRequest


class ActivityReplies(TemplatesCollection):
    current_activity = Template(
        "I'm {activity}",
        activity = ToStrDub(),
    )

    activity_changed = Template(
        "Sure. I'll be busy {activity}",
        activity = ToStrDub()
    )



class ActivityIntents(TemplatesCollection):
    change_activity = Template(
        "Change activity",
        "Do something else"
    )

    activity_request = Template(
        "What are you doing?"
    )

class ActivitySkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(ActivityIntents, ActivityReplies)


    def run(self):
        input: Utterance = yield
        context: KaiaContext = yield ContextRequest()
        if input in ActivityIntents.change_activity:
            yield from context.avatar_api.narration_randomize_activity()
            activity = context.avatar_api.state_get().get(KnownFields.activity, None)
            if activity is not None:
                yield ActivityReplies.activity_changed(activity)
        if input in ActivityIntents.activity_request:
            activity = context.avatar_api.state_get().get(KnownFields.activity, None)
            if activity is not None:
                yield ActivityReplies.current_activity(activity)












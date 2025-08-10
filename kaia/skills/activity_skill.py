from typing import *
from grammatron import *
from kaia import KaiaContext, ContextRequest, World, NarrationService, State, SingleLineKaiaSkill

ACTIVITY = VariableDub("activity", description=f"Activity {World.character} can be doing")

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
        context = yield ContextRequest()
        context = cast(KaiaContext, context)
        if input in ActivityIntents.change_activity:
            state = context.get_client().run_synchronously(NarrationService.ChangeActivityCommand(), State, 1)
            if state.activity is not None:
                yield ActivityReplies.activity_changed(state.activity)
        if input in ActivityIntents.activity_request:
            state = context.get_state()
            if state.activity is not None:
                yield ActivityReplies.current_activity(state.activity)












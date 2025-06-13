from dataclasses import dataclass, field
from ..state import WorldFields, State
from ..image_service import ImageService, ImageMemoryItem
from ..dubbing_service import TextLike
import numpy as np
from brainbox import File
from datetime import datetime



@dataclass
class NarrationSettings:
    characters: tuple[str,...]|None = None
    activities: tuple[str,...]|None = None
    welcome_utterance: TextLike|None = None
    time_between_images_in_seconds: int|None = None
    randomize: bool = True

class NarrationReply:
    @dataclass
    class Item:
        image: File|None = None
        utterance: TextLike|None = None

    def __init__(self):
        self._items: list[NarrationReply.Item] = []

    def __iter__(self):
        for value in self._items:
            if value.image is not None:
                yield value.image
            if value.utterance is not None:
                yield value.utterance


class NarrationService:
    def __init__(self,
                 settings: NarrationSettings,
                 image_service: ImageService|None = None
                 ):
        self.settings = settings
        self.image_service = image_service

    def reset(self, state: State) -> NarrationReply:
        return self.randomize_character(state)

    def _random_change(self, current, collection:tuple|None) -> str|None:
        if collection is None:
            return None
        if self.settings.randomize:
            others = [c for c in collection if c != current]
            if len(others) == 0:
                return None
            idx = np.random.randint(0, len(others))
            if idx>=len(others):
                idx = len(others) - 1
            return others[idx]
        if current in collection:
            idx = collection.index(current)
            return collection[(idx+1)%len(collection)]
        else:
            return collection[0]

    def randomize_character(self, state: State) -> NarrationReply:
        next_character = self._random_change(state.get_state()[WorldFields.character], self.settings.characters)
        if next_character is None:
            return NarrationReply()
        change = {WorldFields.character: next_character}
        next_activity = self._random_change(state.get_state().get(WorldFields.activity, None), self.settings.activities)
        if next_activity is not None:
            change[WorldFields.activity] = next_activity

        return self.apply_state_change(state, change)

    def randomize_activity(self, state: State) -> NarrationReply:
        next_activity = self._random_change(state.get_state().get(WorldFields.activity, None), self.settings.activities)
        if next_activity is None:
            return NarrationReply()

        return self.apply_state_change(state, {WorldFields.activity: next_activity})

    def apply_state_change(self, state: State, change: dict[str, str]) -> NarrationReply:
        current = state.get_state()
        change_image = False
        image_changing_fields = {WorldFields.activity, WorldFields.character}
        add_greeting = False

        for key, value in change.items():
            if key in image_changing_fields:
                if current.get(key, None) != value:
                    change_image = True
            if key == WorldFields.character:
                add_greeting = True
        state.apply_change(change)
        result = NarrationReply()

        if change_image and self.image_service is not None:
            next_image = self.image_service.get_new_image(state)
            result._items.append(NarrationReply.Item(image=next_image))

        if add_greeting and self.settings.welcome_utterance is not None:
            result._items.append(NarrationReply.Item(utterance=self.settings.welcome_utterance))

        return result

    def tick(self, state: State) -> NarrationReply:
        if self.image_service is None:
            return NarrationReply()
        if self.settings.time_between_images_in_seconds is None:
            return NarrationReply()

        last_image_change: ImageMemoryItem | None = (
            state
            .iterate_memory_reversed()
            .where(lambda z: isinstance(z, ImageMemoryItem))
            .first_or_default()
        )
        if last_image_change is None:
            return self.randomize_activity(state)
        delta = datetime.now() - last_image_change.timestamp
        if delta.total_seconds() > self.settings.time_between_images_in_seconds:
            return self.randomize_activity(state)
        return NarrationReply()






















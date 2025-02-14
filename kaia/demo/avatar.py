import os
from kaia.avatar import (
    AvatarServer, AvatarSettings, OpenTTSTaskGenerator, ImageServiceSettings,
    MediaLibraryManager,
    NewContentStrategy, GoodContentStrategy, AnyContentStrategy, WeightedStrategy, SequentialStrategy,
    AvatarApi, InitialStateFactory,
    NarrationSettings
)
from kaia.avatar import World
from pathlib import Path
from .app import KaiaApp
from kaia.skills.character_skill import ChangeCharacterReplies

characters = ['Forest', 'Ocean', 'Mountain', 'Meadow']


def set_avatar_service_and_api(app: KaiaApp):
    os.makedirs(app.folder/'avatar', exist_ok=True)

    image_strategy = SequentialStrategy(
        WeightedStrategy(
            WeightedStrategy.Item(GoodContentStrategy(), 0.3),
            WeightedStrategy.Item(NewContentStrategy(), 0.7),
        ),
        NewContentStrategy(),
        AnyContentStrategy(),
    )
    image_manager = MediaLibraryManager(
        image_strategy,
        Path(__file__).parent/'files/image_library.zip',
        app.folder/'avatar'/'stats.json'
    )
    image_settings = ImageServiceSettings(
        image_manager,
        None
    )

    character_to_voice = {'Meadow': 'p225', 'Forest': 'p229', 'Mountain': 'p230', 'Ocean': 'p237'}

    narration_settings = NarrationSettings(
        tuple(characters),
        welcome_utterance=ChangeCharacterReplies.hello()
    )

    settings = AvatarSettings(
        initial_state_factory=InitialStateFactory.Simple({World.character.field_name:'Lina'}),
        dubbing_task_generator=OpenTTSTaskGenerator(character_to_voice),
        image_settings=image_settings,
        errors_folder=app.folder/'/avatar/errors',
        brain_box_api=app.brainbox_api,
        narration_settings=narration_settings,
    )
    app.avatar_server = AvatarServer(settings)
    app.avatar_api = AvatarApi(f'127.0.0.1:{settings.port}')



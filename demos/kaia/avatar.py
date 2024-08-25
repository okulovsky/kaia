from kaia.brainbox import BrainBoxApi
from kaia.infra import Loc
from kaia.avatar import (
    AvatarWebServer, AvatarSettings, OpenTTSTaskGenerator,
    MediaLibraryManager,
    NewContentStrategy, GoodContentStrategy, AnyContentStrategy, WeightedStrategy, SequentialStrategy,
    AvatarAPI
)
from kaia.narrator import SimpleNarrator

from pathlib import Path

characters = ['Lina', 'Jug']


def create_avatar_service_and_api(brain_box_api: BrainBoxApi):
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
        Loc.data_folder / 'demo/avatar/images/new_stats.json'
    )

    character_to_voice = {'Lina': 'p225', 'Jug': 'p229'}

    narrator = SimpleNarrator('Lina')


    settings = AvatarSettings(
        narrator=narrator,
        dubbing_task_generator=OpenTTSTaskGenerator(character_to_voice),
        image_media_library_manager=image_manager,
        errors_folder=Loc.data_folder/'demo/avatar/errors',
        brain_box_api=brain_box_api
    )
    avatar_server = AvatarWebServer(settings)
    return avatar_server, AvatarAPI(f'127.0.0.1:{settings.port}')


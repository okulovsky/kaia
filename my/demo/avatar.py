from kaia.brainbox import BrainBoxWebApi
from kaia.infra import Loc
from kaia.avatar.server import (
    AvatarWebServer, BrainBoxDubbingService, AvatarSettings, open_tts_task_generator,
    ImageService, NewImageStrategy, GoodImageStrategy, AnyImageStrategy, ImageStrategyWithWeight, CombinedStrategy,
    AvatarAPI
)
from .narration import create_narrator
from pathlib import Path


def create_avatar_service_and_api(brain_box_api: BrainBoxWebApi):
    settings = AvatarSettings()

    image_strategy = CombinedStrategy(
        (
            ImageStrategyWithWeight(GoodImageStrategy(), 0.3),
            ImageStrategyWithWeight(NewImageStrategy(), 0.7),
        ),
        (
            NewImageStrategy(),
            AnyImageStrategy()
        )
    )

    image_service = ImageService(
        image_strategy,
        Path(__file__).parent/'files/image_library.zip',
        Loc.data_folder / 'demo/avatar/images/new_stats.json'
    )

    dubbing_service = BrainBoxDubbingService(open_tts_task_generator, brain_box_api)
    avatar_server = AvatarWebServer(
        settings,
        create_narrator(),
        dubbing_service,
        image_service,
        Loc.data_folder / 'demo/avatar/errors'
    )
    return avatar_server, AvatarAPI(f'127.0.0.1:{settings.port}')


from pathlib import Path
from foundation_kaia.marshalling import Serializer
from avatar.daemon.common.content import Feedback, StorageFeedbackStorage
from avatar.daemon.image_service import ImageService, ImageLibraryLoader, ImageRecord
from chara import Chara
from .dto import ActivityStatistics, ImageSetupStatistics
from ..activity import ImageSetup, ImageSetupFingerprint, ImageFingerprint, ActivityCatalogItem

_Stats = dict[ImageSetupFingerprint, ImageSetupStatistics]



class ImageStatisticsPipeline:
    def __init__(self, activities_path: Path, service_to_read: type = ImageService):
        self.activities_path = activities_path
        self.service_to_read = service_to_read

    def __call__(self, setups: list[ImageSetup]) -> list[ImageSetupStatistics]:
        stats = Chara.call(self._seed_from_catalog, 'seed_from_catalog')(setups)
        records = Chara.call(self._load_records, 'loading_descriptions')()
        feedback = Feedback(Chara.call(self._load_feedback)())

        fp_to_stats = {s.setup.to_fingerprint(): s for s in stats}
        serializer = Serializer.parse(ImageFingerprint)

        for record in records:
            fingerprint = serializer.from_json(record.description['image_fingerprint'])
            setup_stats = fp_to_stats.get(fingerprint.setup_fingerprint)
            if setup_stats is None:
                continue

            if fingerprint.activity not in setup_stats.activity_status:
                setup_stats.activity_status[fingerprint.activity] = ActivityStatistics()
            activity_stats = setup_stats.activity_status[fingerprint.activity]

            activity_stats.generated += 1
            activity_stats.seen += feedback.get(record.file_id, 'seen')
            activity_stats.good += feedback.get(record.file_id, 'good')
            activity_stats.bad += feedback.get(record.file_id, 'bad')

        return stats

    def _seed_from_catalog(self, setups: list[ImageSetup]) -> list[ImageSetupStatistics]:
        catalog = ActivityCatalogItem.read_catalog(self.activities_path)
        result = []
        for setup in setups:
            fingerprint = setup.to_fingerprint()
            item = catalog.get(fingerprint)
            activities = item.activities if item is not None else []
            result.append(ImageSetupStatistics(
                setup,
                {activity: ActivityStatistics() for activity in activities},
            ))
        return result

    def _load_records(self) -> list[ImageRecord]:
        # local_folder is None: the zips stay on the avatar machine, only the descriptions
        # are read. Neither the loader nor a Feedback may be returned from a Chara.call -
        # both hold an HTTP client, and the result gets pickled into the cache folder.
        loader = ImageLibraryLoader(
            Chara.Apis.avatar_api.resources(self.service_to_read),
            None,
            self.service_to_read.DESCRIPTION_SUFFIX,
        )
        return loader.get_records()

    def _load_feedback(self) -> dict:
        storage = StorageFeedbackStorage(
            Chara.Apis.avatar_api.resources(self.service_to_read),
            ImageLibraryLoader.FEEDBACK_FILENAME,
        )
        return storage.load().to_dict()

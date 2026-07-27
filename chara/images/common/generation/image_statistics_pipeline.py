import json
from pathlib import Path
from foundation_kaia.marshalling import Serializer
from avatar.daemon.image_service import ImageService
from chara import Chara
from .dto import MediaLibraryDescriptionItem, ActivityStatistics, ImageSetupStatistics
from ..activity import ImageSetup, ImageSetupFingerprint, ImageFingerprint, ActivityCatalogItem

_Stats = dict[ImageSetupFingerprint, ImageSetupStatistics]



class ImageStatisticsPipeline:
    def __init__(self, activities_path: Path, service_to_read: type = ImageService):
        self.activities_path = activities_path
        self.service_to_read = service_to_read

    def __call__(self, setups: list[ImageSetup]) -> list[ImageSetupStatistics]:
        stats = Chara.call(self._seed_from_catalog, 'seed_from_catalog')(setups)
        descriptions = Chara.call(self._load_descriptions, 'loading_descriptions')()

        fp_to_stats = {s.setup.to_fingerprint():s for s in stats}
        file_to_fp = {}
        for desc in descriptions:
            file_to_fp[desc.file_id] = desc.image_fingerprint
            setup_stats = fp_to_stats.get(desc.image_fingerprint.setup_fingerprint)
            if setup_stats is not None:
                if desc.image_fingerprint.activity not in setup_stats.activity_status:
                    setup_stats.activity_status[desc.image_fingerprint.activity] = ActivityStatistics()
                setup_stats.activity_status[desc.image_fingerprint.activity].generated += 1

        feedback = Chara.call(self._load_feedback)()

        for file_id, tags in feedback.items():
            fingerprint = file_to_fp.get(file_id)
            if fingerprint is None:
                continue

            setup_stats = fp_to_stats.get(fingerprint.setup_fingerprint)
            if setup_stats is None:
                continue

            activity_stats = setup_stats.activity_status.get(fingerprint.activity)
            if activity_stats is None:
                continue

            activity_stats.seen += tags.get('seen', 0)
            activity_stats.good += tags.get('good', 0)
            activity_stats.bad += tags.get('bad', 0)

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

    def _load_descriptions(self) -> list[MediaLibraryDescriptionItem]:
        resources = Chara.Apis.avatar_api.resources(self.service_to_read)
        result = []
        serializer = Serializer.parse(list[MediaLibraryDescriptionItem])

        for filename in resources.list('/', suffix=self.service_to_read.DESCRIPTION_SUFFIX):
            data = json.loads(resources.read(filename))
            for item in data:
                # Only file_id/image_fingerprint are used below - `case` is dropped
                # before deserializing so old entries don't break as the scenario
                # schema (deep inside `case`) evolves.
                item.pop('case', None)
            result.extend(serializer.from_json(data))
        return result

    def _load_feedback(self):
        resources = Chara.Apis.avatar_api.resources(self.service_to_read)
        if not resources.is_file('images-feedback.json'):
            return {}

        feedback = json.loads(resources.read('images-feedback.json'))
        return feedback


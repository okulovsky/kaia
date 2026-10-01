import json
from pathlib import Path
from loguru import logger
from foundation_kaia.marshalling import IStorage
from ..common.content import StorageFeedbackStorage
from .image_record import ImageRecord, VariantRecord


class ImageLibraryLoader:
    DESCRIPTION_SUFFIX = '.description.json'
    FEEDBACK_FILENAME = 'images-feedback.json'

    def __init__(self,
                 storage: IStorage,
                 local_folder: Path|None = None,
                 description_suffix: str = DESCRIPTION_SUFFIX,
                 feedback_filename: str = FEEDBACK_FILENAME,
                 ):
        self.storage = storage
        self.local_folder = local_folder
        self.description_suffix = description_suffix
        self.feedback_storage = StorageFeedbackStorage(storage, feedback_filename)
        self.records = self._load()
        self._by_id = {record.file_id: record for record in self.records}

    def _load(self) -> list[ImageRecord]:
        records: list[ImageRecord] = []
        variants: list[tuple[str, VariantRecord]] = []

        for filename in sorted(self.storage.list('.', suffix=self.description_suffix)):
            zip_path = None
            if self.local_folder is not None:
                zip_path = self.local_folder / filename[:-len(self.description_suffix)]
            for entry in json.loads(self.storage.read(filename)):
                if 'variant' in entry:
                    variants.append((
                        entry['variant']['original'],
                        VariantRecord(
                            file_id=entry['file_id'],
                            variant_type=entry['variant']['variant_type'],
                            zip_path=zip_path,
                        )
                    ))
                else:
                    records.append(ImageRecord(
                        file_id=entry['file_id'],
                        tags=entry.get('tags') or {},
                        description=entry,
                        zip_path=zip_path,
                    ))

        by_id = {record.file_id: record for record in records}
        for original, variant in variants:
            if original not in by_id:
                logger.warning(f"Variant {variant.file_id} refers to the missing original {original} and is dropped")
                continue
            by_id[original].variants.append(variant)

        return records

    def get_records(self) -> list[ImageRecord]:
        return self.records

    def get_record(self, file_id: str) -> ImageRecord|None:
        return self._by_id.get(file_id)

    def get_variants(self, file_id: str, variant_type: str) -> list[VariantRecord]:
        record = self._by_id.get(file_id)
        if record is None:
            return []
        return [variant for variant in record.variants if variant.variant_type == variant_type]

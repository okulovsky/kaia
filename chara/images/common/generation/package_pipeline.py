import json
from chara import CaseCollection, Chara
from chara.common.pipelines import upload_to_avatar
from foundation_kaia.marshalling import Serializer
from ..drawing import DrawingCase
from .dto import MediaLibraryDescriptionItem
from ..activity import ImageSetup, ImageFingerprint
from avatar.daemon import ImageService
from avatar.daemon.image_service.media_library import MediaLibrary


class PackagePipeline:
    def __init__(self,
                 service_to_upload: type = ImageService,
                 index_length: int = 4,
                 ):
        self.service_to_upload = service_to_upload
        self.index_length = index_length

    def __call__(self, cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        records = []
        files = []
        descriptions = []

        for case in cases.successes:
            fingerprint = ImageSetup(case.scenario.character, case.scenario.theme).to_fingerprint()
            image_fingerprint = ImageFingerprint(fingerprint, case.scenario.activity)
            tags = image_fingerprint.to_tags()

            main_record = MediaLibrary.Record(path=case.image.name, tags=tags)
            records.append(main_record)
            files.append(case.image)

            for key, variant in (case.variants or {}).items():
                records.append(MediaLibrary.Record(
                    path=variant.image.name,
                    tags={'original': main_record.path, 'variant_type': key},
                ))
                files.append(variant.image)

            descriptions.append(MediaLibraryDescriptionItem(
                file_id=main_record.path,
                image_fingerprint=image_fingerprint,
                case=case,
            ))

        path = Chara.current.folder / 'media_library.zip'
        MediaLibrary.save(path, records, files)

        media_library_filename = upload_to_avatar(
            self.service_to_upload,
            self.service_to_upload.MEDIA_LIBRARY_PREFIX,
            self.service_to_upload.MEDIA_LIBRARY_SUFFIX,
            self.index_length,
            path
        )

        serializer = Serializer.parse(list[MediaLibraryDescriptionItem])
        description_data = json.dumps(serializer.to_json(descriptions)).encode('utf-8')
        Chara.Apis.avatar_api.resources(self.service_to_upload).upload(
            media_library_filename+self.service_to_upload.DESCRIPTION_SUFFIX,
            description_data,
        )

        return cases

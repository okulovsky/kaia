import json
import zipfile
from chara import CaseCollection, Chara
from chara.common.pipelines import upload_to_avatar
from foundation_kaia.marshalling import Serializer
from foundation_kaia.marshalling.protocol.model.file_like import FileLike, FileLikeHandler
from ..drawing import DrawingCase
from .dto import MediaLibraryDescriptionItem
from ..activity import ImageSetup, ImageFingerprint
from avatar.daemon import ImageService


class PackagePipeline:
    def __init__(self,
                 service_to_upload: type = ImageService,
                 index_length: int = 4,
                 ):
        self.service_to_upload = service_to_upload
        self.index_length = index_length

    def __call__(self, cases: CaseCollection[DrawingCase]) -> CaseCollection[DrawingCase]:
        files = []
        descriptions = []
        variant_entries = []

        for case in cases.successes:
            fingerprint = ImageSetup(case.scenario.character, case.scenario.theme).to_fingerprint()
            image_fingerprint = ImageFingerprint(fingerprint, case.scenario.activity)

            files.append(case.image)
            descriptions.append(MediaLibraryDescriptionItem(
                file_id=case.image.name,
                image_fingerprint=image_fingerprint,
                case=case,
                tags=image_fingerprint.to_tags(),
            ))

            for key, variant in (case.variants or {}).items():
                files.append(variant.image)
                variant_entries.append({
                    'file_id': variant.image.name,
                    'variant': {'original': case.image.name, 'variant_type': key},
                })

        path = Chara.current.folder / 'media_library.zip'
        self._write_zip(path, files)

        media_library_filename = upload_to_avatar(
            self.service_to_upload,
            self.service_to_upload.MEDIA_LIBRARY_PREFIX,
            self.service_to_upload.MEDIA_LIBRARY_SUFFIX,
            self.index_length,
            path
        )

        serializer = Serializer.parse(list[MediaLibraryDescriptionItem])
        description_data = json.dumps(serializer.to_json(descriptions) + variant_entries).encode('utf-8')
        Chara.Apis.avatar_api.resources(self.service_to_upload).upload(
            media_library_filename+self.service_to_upload.DESCRIPTION_SUFFIX,
            description_data,
        )

        return cases

    @staticmethod
    def _write_zip(path, files: list[FileLike]) -> None:
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zp:
            for file in files:
                zp.writestr(FileLikeHandler.guess_name(file), FileLikeHandler.to_bytes(file))

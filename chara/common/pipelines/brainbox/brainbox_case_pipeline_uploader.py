from typing import Generic

from ...architecture import Chara, logger
from ..cases import TCase
from foundation_kaia.marshalling import FileLikeHandler, FileLike
from brainbox.framework import ControllerRegistry
from typing import Any
from dataclasses import dataclass

@dataclass
class BrainBoxCaseResourceUpload:
    resource: Any
    target_path: str
    file: FileLike

@dataclass
class UploadedFiles:
    cache: set[str]
    resources: dict[str, set[str]]



class BrainBoxCasePipelineUploader(Generic[TCase]):
    ResourceUpload = BrainBoxCaseResourceUpload

    def __init__(self, case_to_file_like, remove_after: bool = True):
        self.case_to_file_like = case_to_file_like
        self.remove_after = remove_after

    def _acceptable(self, obj):
        return FileLikeHandler.is_file_like(obj) or isinstance(obj, BrainBoxCaseResourceUpload)

    def upload(self, cases: tuple[TCase,...]) -> UploadedFiles:
        uploads = UploadedFiles(set(), {})

        for case in cases:
            obj = self.case_to_file_like(case)
            if self._acceptable(obj):
                to_upload = [obj]
            else:
                to_upload = list(obj)
                for i, f in enumerate(to_upload):
                    if not self._acceptable(f):
                        raise ValueError(f"If a collection is returned, every element must be filelike or resource upload, but at index {i} was {f}")
            for u in to_upload:
                if FileLikeHandler.is_file_like(u):
                    name = FileLikeHandler.guess_name(u)
                    if name not in uploads.cache:
                        Chara.Apis.brainbox_api.cache.upload(name, u)
                        uploads.cache.add(name)
                elif isinstance(u, BrainBoxCaseResourceUpload):
                    resource_name = ControllerRegistry.to_controller_name(u.resource)
                    if resource_name not in uploads.resources:
                        uploads.resources[resource_name] = set()
                    if u.target_path not in uploads.resources[resource_name]:
                        Chara.Apis.brainbox_api.resources(u.resource).upload(u.target_path, u.file)
                        uploads.resources[resource_name].add(u.target_path)

        logger.info(f"{len(uploads.cache)} files uploaded to brainbox cache")
        resources_uploads = sum(len(c) for c in uploads.resources.values())
        logger.info(f"{resources_uploads} files uploaded to brainbox resources")

        return uploads


    def cleanup(self, uploads: UploadedFiles):
        if self.remove_after:
            for name in uploads.cache:
                Chara.Apis.brainbox_api.cache.delete(name)
            logger.info(f"{len(uploads.cache)} files removed from cache")
            cnt = 0
            for resource in uploads.resources:
                for name in uploads.resources[resource]:
                    Chara.Apis.brainbox_api.resources(resource).delete(name)
                    cnt += 1
            logger.info(f"{cnt} files removed from brainbox resources")






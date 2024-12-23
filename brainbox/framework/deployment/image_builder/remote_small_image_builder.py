from .small_image_builder import SmallImageBuilder
from .image_builder import IImageBuilder
from ..executor import IExecutor
from pathlib import Path
from uuid import uuid4

class RemoteSmallImageBuilder(IImageBuilder):
    def __init__(self,
                 inner_builder: SmallImageBuilder,
                 tmp_folder: Path,
    ):
        self.inner_builder = inner_builder
        self.tmp_folder = tmp_folder

    def build_image(self, image_name: str, executor: IExecutor) -> None:
        from yo_fluq_ds import Query

        self.inner_builder._prepare_container_folder(executor)
        remote_folder = self.tmp_folder/str(uuid4())
        for file_ in Query.folder(self.inner_builder.code_path, '**/*'):
            file: Path = file_
            if not file.is_file():
                continue
            rel_path = file.relative_to(self.inner_builder.code_path)
            remote_path = remote_folder/rel_path
            print(f"copying file {file} -> {remote_path}")
            executor.create_empty_folder(remote_path.parent)
            executor.upload_file(file, str(remote_path))
        executor.execute(['docker','build','-t',image_name,str(remote_folder)])






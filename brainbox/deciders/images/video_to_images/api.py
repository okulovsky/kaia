import shutil
from ....framework import OnDemandDockerApi, ResourcePrerequisite, FileLike
from .controller import VideoToImagesController
from .settings import VideoToImagesSettings
from yo_fluq import Query


class VideoToImages(OnDemandDockerApi[VideoToImagesSettings, VideoToImagesController]):
    def __init__(self):
        pass

    def process(self, file_name: str, cap_result_count: int|None = None):
        config = self.controller.get_run_configuration(['--file', file_name])
        self.controller.get_deployment().stop().remove()
        self.controller.run_with_configuration(config)
        folder = self.controller.resource_folder('output')
        result = {}
        for file in Query.folder(folder):
            name = int(file.name.split('.')[0])
            fname = f'{self.current_job_id}.{name}.png'
            shutil.copy(file, self.cache_folder/fname)
            result[name] = fname
        result = [result[key] for key in sorted(result)]
        if cap_result_count is not None:
            result = result[:cap_result_count]
        return result


    @staticmethod
    def upload_video(file: FileLike.Type):
        return ResourcePrerequisite(
            VideoToImages,
            f'/input/{FileLike.get_name(file,True)}',
            file
        )

    Controller = VideoToImagesController
    Settings = VideoToImagesSettings
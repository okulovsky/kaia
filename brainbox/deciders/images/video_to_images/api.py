import shutil
from ....framework import OnDemandDockerApi, ResourcePrerequisite, FileLike, FileIO

from .controller import VideoToImagesController
from .settings import VideoToImagesSettings
from yo_fluq import Query
import json
from .container.settings import AnalysisSettings

class VideoToImages(OnDemandDockerApi[VideoToImagesSettings, VideoToImagesController]):
    def __init__(self):
        pass

    def _monitor(self, s):
        try:
            number = int(s.split('%')[0])
            self.context.logger.report_progress(number/100)
        except:
            pass


    def process(self, analysis_settings: AnalysisSettings|dict):
        if isinstance(analysis_settings, dict):
            analysis_settings = AnalysisSettings(**analysis_settings)

        FileIO.write_json(analysis_settings.__dict__, self.controller.resource_folder()/'settings.json')
        self.run_container(self.controller.get_run_configuration(), self._monitor)

        folder = self.controller.resource_folder('output/images')

        text = FileIO.read_text(self.controller.resource_folder('output')/'frames.jsonl')
        lines = text.split('\n')
        records = []

        for line in lines:
            if line.strip() == '':
                continue
            try:
                record = json.loads(line)
            except:
                print(f"Error parsing line\n`{line}`")
                continue

            fname = self.current_job_id+'.'+record['filename']
            shutil.move(folder/record['filename'], self.cache_folder / fname)
            record['filename'] = fname
            records.append(record)

        return records


    @staticmethod
    def upload_video(file: FileLike.Type):
        return ResourcePrerequisite(
            VideoToImages,
            f'/input/{FileLike.get_name(file,True)}',
            file
        )

    @staticmethod
    def delete_video(filename: str):
        return ResourcePrerequisite(
            VideoToImages,
            '/input/'+filename,
            None
        )

    Controller = VideoToImagesController
    Settings = VideoToImagesSettings
    AnalysisSettings = AnalysisSettings
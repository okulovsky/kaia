import json
import os
import tarfile
import uuid
from pathlib import Path
from typing import Iterable

from foundation_kaia.marshalling import FileLike, FileLikeHandler
from foundation_kaia.brainbox_utils import BrainboxReportItem, LongBrainboxProcess, logger
from interface import VideoToImagesInterface, AnalysisSettings
from installer import VideoToImagesInstaller



class VideoToImagesProcess(LongBrainboxProcess[list]):
    def __init__(self, video_path: Path, settings: AnalysisSettings):
        self.video_path = video_path
        self.settings = settings

    def execute(self) -> list:
        from algorithm import VideoProcessorApp
        try:
            with open('/resources/settings.json', 'w') as f:
                json.dump(self.settings.__dict__, f)

            logger.info("Processing video")
            VideoProcessorApp().run()

            records = []
            with open('/resources/output/frames.jsonl', 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

            logger.info(f"Building tar with {len(records)} frames")
            os.makedirs('/resources/output', exist_ok=True)
            with tarfile.open('/resources/output/frames.tar', 'w') as tar:
                for record in records:
                    img_path = f'/resources/output/images/{record["filename"]}'
                    if os.path.exists(img_path):
                        tar.add(img_path, arcname=record['filename'])

            return records
        finally:
            self.video_path.unlink(missing_ok=True)


class VideoToImagesService(VideoToImagesInterface):
    def __init__(self, installer: VideoToImagesInstaller):
        self.installer = installer

    def process(self, video: FileLike, settings: AnalysisSettings) -> Iterable[BrainboxReportItem[list]]:
        video_path = Path(f'/resources/input/tmp_{uuid.uuid4()}.mp4')
        video_path.parent.mkdir(parents=True, exist_ok=True)
        FileLikeHandler.write(video, video_path)
        settings.source_file_name = video_path.name
        process = VideoToImagesProcess(video_path, settings)
        return process.start_process('/resources/log.html')

    def get_tar(self) -> FileLike:
        return Path('/resources/output/frames.tar')

from kaia.brainbox.deciders.video_processor.installer import VideoProcessorInstaller
from kaia.brainbox.deciders.video_processor.settings import VideoProcessorSettings

if __name__ == '__main__':
    installer = VideoProcessorInstaller(VideoProcessorSettings)
    installer.run_in_any_case_and_create_api()
from kaia.brainbox.deciders import OpenTTS
from kaia.infra.ffmpeg import FFmpegTools
from kaia.infra import Loc
from kaia.brainbox import BrainBox
from kaia.brainbox.deciders import FunctionalTaskGenerator
from pathlib import Path
from yo_fluq_ds import *




if __name__ == '__main__':
    silence_path = FFmpegTools.create_silence_audio(Loc.data_folder/'silence_1s.wav', 2)

    pack = (
        Query
        .en(['one', 'two', 'three'])
        .select(lambda z: 'fragment number '+z)
        .feed(FunctionalTaskGenerator(
            lambda z: BrainBox.Task.call(OpenTTS).voiceover(z).to_task(),
            method='to_array'
        )))
    with BrainBox().create_test_api() as api:
        result = api.execute(pack)
        to_concat = [silence_path]
        for file in result:
            to_concat.append(api.cache_folder/file['result'].name)
            to_concat.append(silence_path)
        FFmpegTools.concat_audio_with_ffmpeg(to_concat, Path(__file__).parent/'sound.wav')


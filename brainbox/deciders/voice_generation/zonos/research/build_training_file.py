from yo_fluq import *
from pathlib import Path
from brainbox import BrainBox
from brainbox.framework import Loc
from brainbox.deciders import Ffmpeg




if __name__ == '__main__':
    path = Path(__file__).parent.parent.parent/'piper_training/files'
    files = Query.folder(path,'*.wav').to_list()
    with BrainBox.Api.Test() as api:
        result = api.execute(BrainBox.Task.call(Ffmpeg).concat(files, '.mp3'))
        api.download(result, Path(__file__).parent/'lina.mp3')

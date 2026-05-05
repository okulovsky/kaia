from brainbox.deciders import Whisper
from brainbox import BrainBox
from pathlib import Path


def transcribe_files_in_folder(path: Path, api: BrainBox.Api):
    files = list(enumerate(path.glob("*.wav")))
    for index, file in files:
        print(f"{index}/{len(files)}: {file.name}")
        result = api.execute(Whisper.new_task().transcribe_text(file))
        output = str(file)+".transcription"
        Path(output).write_text(result)






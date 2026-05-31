from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


def separate_file(
    video_path: Path,
    output_folder: Path,
    min_silence_len: int = 500,
    silence_thresh: int = -60,
):
    video_path = Path(video_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    audio = AudioSegment.from_file(str(video_path))

    ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)

    for i, (start_ms, end_ms) in enumerate(ranges):
        clip = audio[start_ms:end_ms]
        clip.export(str(output_folder / f"{i:03d}.wav"), format="wav")

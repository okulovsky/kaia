import argparse
import json
import subprocess
import sys
from pathlib import Path
import whisperx
import torch

def append_dict_to_json_array(file_path, data):
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_models(args, device):
    model = whisperx.load_model(args.model, device=device, compute_type=args.compute_type,
                                download_root="/resources/models/")
    model_a, metadata = whisperx.load_align_model(
        language_code='ru',
        device=device
    )
    diarize_model = whisperx.diarize.DiarizationPipeline(
        use_auth_token=args.hf_token,
        device=device
    )

    return model, diarize_model, model_a, metadata

def handle_video(args, input_dir, output_dir):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, diarize_model, model_a, metadata = load_models(args, device)
    for video_path in input_dir.rglob('*.mp4'):
        audio = whisperx.load_audio(str(video_path))
        result = model.transcribe(audio, language=args.language, batch_size=16)
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            device,
            return_char_alignments=False
        )
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)
        for segment in result["segments"]:
            segment.pop('words')
        result_with_meta = {
            "file": video_path.name,
            "segments": result["segments"]
        }
        append_dict_to_json_array(output_dir / 'output.json', result_with_meta)

def create_parser():
    parser = argparse.ArgumentParser(
        description="Video file processing with transcription and details"
    )

    parser.add_argument('-n', '--notebook', action='store_true')
    parser.add_argument('-i', '--input_dir', type=str, default='/resources/files')
    parser.add_argument('-o', '--output_dir', type=str, default='/resources/output')
    parser.add_argument('-m', '--model', type=str, choices=['base', 'large-v2'], default='base')
    parser.add_argument('--download_root', type=str, default='/resources/models')
    parser.add_argument('-t', '--compute_type', type=str, default='float32')
    parser.add_argument('-l', '--language', type=str, default='ru')
    # Здесь вставьте токен с huggingface, чтобы модель подгружалась без проблем: https://huggingface.co/settings/tokens
    parser.add_argument('--hf_token', type=str, default='')

    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    print(f'Running with arguments {args}')

    if args.notebook:
        subprocess.call([sys.executable, '-m', 'notebook', '--allow-root', '--port', '8899', '--ip', '0.0.0.0',
                         "--NotebookApp.token=''"], cwd='/repo')
        exit(0)

    input_dir, output_dir = Path(args.input_dir), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    handle_video(args, input_dir, output_dir)
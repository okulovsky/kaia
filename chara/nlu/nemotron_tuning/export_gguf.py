"""
Converts a model merged by train_lora.py into the GGUF of NeMo-Speech.cpp, the runtime of the Nemotron decider.

    python chara/nlu/nemotron_tuning/export_gguf.py --merged <run>/merged --out <run>/nemotron-tuned.q8_0.gguf \
        --nemo-speech <checkout of NVIDIA/NeMo-Speech.cpp> --converter-python <its venv>/bin/python

convert_model.py of NeMo-Speech.cpp reads .nemo, and the names of the weights in Transformers and in NeMo differ.
So the merged weights are put into a copy of the original .nemo by a mapping found on the original weights:
each NeMo tensor is matched to the Transformers tensor with the same values. On the original model this gives
a GGUF whose 657 tensors are identical to the published one, i.e. the conversion loses nothing.
The checkout of NeMo-Speech.cpp must be at the commit of the decider (NEMO_SPEECH_COMMIT below).
"""
import argparse
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open

MODEL = 'nvidia/nemotron-3.5-asr-streaming-0.6b'
REVISION = 'ea30d66debe3740a08b573244286791d423d6b3e'
# brainbox/deciders/voice_analysis/nemotron/controller.py builds the runtime from this commit
NEMO_SPEECH_COMMIT = '4c101bc7113f49101a3e11d2c994c519f41939f6'


class LazyTensors:
    """The tensors of a safetensors file, read one at a time: both checkpoints are 2.5 GB"""
    def __init__(self, path: Path):
        self.file = safe_open(str(path), framework='pt')

    def keys(self) -> list[str]:
        return list(self.file.keys())

    def shape(self, name: str) -> tuple:
        return tuple(self.file.get_slice(name).get_shape())

    def __getitem__(self, name: str) -> torch.Tensor:
        return self.file.get_tensor(name)


def read_nemo(path: Path, work: Path) -> tuple[dict, str]:
    """The state dict of the .nemo, memory-mapped from a copy in `work`, and its name inside the archive"""
    copy = work/'model_weights.ckpt'
    with tarfile.open(path) as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith('model_weights.ckpt'))
        with tar.extractfile(member) as source, open(copy, 'wb') as target:
            while chunk := source.read(1 << 24):
                target.write(chunk)
    return torch.load(copy, map_location='cpu', weights_only=True, mmap=True), member.name


def variants(tensor: torch.Tensor):
    yield 'same', tensor
    if tensor.dim() == 3 and tensor.shape[-1] == 1:
        yield 'squeeze', tensor.squeeze(-1)
    if tensor.dim() == 2:
        yield 'transpose', tensor.t()


def find_mapping(nemo: dict, hf: LazyTensors) -> dict:
    """NeMo name -> (Transformers name, how it is stored); fails if a trained tensor has no match"""
    by_shape = {}
    for name in hf.keys():
        by_shape.setdefault(hf.shape(name), []).append(name)
    used, mapping = set(), {}
    for nemo_name, tensor in nemo.items():
        if not torch.is_floating_point(tensor):
            continue
        found = None
        for how, candidate in variants(tensor):
            for hf_name in by_shape.get(tuple(candidate.shape), []):
                if hf_name not in used and torch.equal(hf[hf_name].to(candidate.dtype), candidate):
                    found = (hf_name, how)
                    break
            if found:
                break
        if found:
            used.add(found[0])
            mapping[nemo_name] = found
    unused = set(hf.keys()) - used
    if unused:
        raise ValueError(f'Transformers tensors without a NeMo counterpart: {sorted(unused)[:10]}')
    return mapping


def write_nemo(source: Path, merged: LazyTensors, mapping: dict, out: Path, work: Path):
    nemo, weights_name = read_nemo(source, work)
    for nemo_name, (hf_name, how) in mapping.items():
        tensor = merged[hf_name].to(nemo[nemo_name].dtype)
        if how == 'squeeze':
            tensor = tensor.unsqueeze(-1)
        elif how == 'transpose':
            tensor = tensor.t()
        nemo[nemo_name] = tensor.contiguous()
    buffer = io.BytesIO()
    torch.save(nemo, buffer)
    with tarfile.open(source) as tar_in, tarfile.open(out, 'w') as tar_out:
        for member in tar_in.getmembers():
            if member.name == weights_name:
                info = tarfile.TarInfo(member.name)
                info.size = buffer.tell()
                buffer.seek(0)
                tar_out.addfile(info, buffer)
            else:
                tar_out.addfile(member, tar_in.extractfile(member) if member.isfile() else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--merged', required=True, help='the folder of the merged model (model.safetensors)')
    parser.add_argument('--out', required=True, help='the GGUF to write')
    parser.add_argument('--nemo-speech', required=True, help=f'checkout of NVIDIA/NeMo-Speech.cpp at {NEMO_SPEECH_COMMIT[:7]}')
    parser.add_argument('--converter-python', required=True, help='python of an environment with its requirements.txt')
    parser.add_argument('--outtype', default='q8_0', help='the published model is q8_0')
    args = parser.parse_args()

    commit = subprocess.run(['git', '-C', args.nemo_speech, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if commit != NEMO_SPEECH_COMMIT:
        print(f'Warning: NeMo-Speech.cpp is at {commit[:7]}, the decider runs {NEMO_SPEECH_COMMIT[:7]}')
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    source = Path(hf_hub_download(MODEL, 'nemotron-3.5-asr-streaming-0.6b.nemo', revision=REVISION))
    mapping_file = out.parent/'nemo_mapping.json'
    with tempfile.TemporaryDirectory(dir=out.parent) as work:
        work = Path(work)
        if mapping_file.exists():
            mapping = json.loads(mapping_file.read_text())
        else:
            print('Finding the mapping of the weights on the original model...')
            original, _ = read_nemo(source, work)
            mapping = find_mapping(original, LazyTensors(Path(hf_hub_download(MODEL, 'model.safetensors', revision=REVISION))))
            mapping_file.write_text(json.dumps(mapping, indent=1))
        print(f'{len(mapping)} tensors are mapped')
        nemo = work/'merged.nemo'
        write_nemo(source, LazyTensors(Path(args.merged)/'model.safetensors'), mapping, nemo, work)
        subprocess.run([args.converter_python, 'convert_model.py', str(nemo), '--outfile', str(out), '--outtype', args.outtype],
                       cwd=args.nemo_speech, check=True)
    print(f'{out} ({out.stat().st_size / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()

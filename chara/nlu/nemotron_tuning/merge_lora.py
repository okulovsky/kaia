"""
Merges an adapter of train_lora.py into the weights, at a strength below 1 if needed. The harm to real speech grows faster
than the gain, so a weaker adapter can keep most of the gain and none of the harm, see the README.

    python chara/nlu/nemotron_tuning/merge_lora.py --adapter <run>/adapter --strength 0.4 --out <run>/merged-0.4
"""
import argparse
from pathlib import Path
import torch
from peft import PeftModel
from peft.tuners.lora import LoraLayer
from transformers import AutoProcessor, Nemotron3_5AsrForRNNT
from manifest import MODEL, REVISION


def merge(adapter: Path, strength: float, out: Path):
    """The same architecture and names as the base model, which export_gguf.py relies on"""
    model = PeftModel.from_pretrained(Nemotron3_5AsrForRNNT.from_pretrained(MODEL, revision=REVISION, dtype=torch.float32), adapter)
    for module in model.modules():
        if isinstance(module, LoraLayer):
            for name in module.scaling:
                module.scaling[name] *= strength
    model.merge_and_unload().save_pretrained(out)
    AutoProcessor.from_pretrained(MODEL, revision=REVISION).save_pretrained(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', required=True)
    parser.add_argument('--strength', type=float, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    merge(Path(args.adapter), args.strength, Path(args.out))
    print(f'adapter at strength {args.strength} merged into {args.out}')


if __name__ == '__main__':
    main()

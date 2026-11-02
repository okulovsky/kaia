"""
Merges an adapter of train_lora.py into the weights at a strength below 1. The harm to real speech grows faster than the gain,
so a weaker adapter can keep most of the gain and none of the harm, see the README. Run it from chara/nlu/nemotron_tuning.

    python merge_lora.py --adapter <run>/adapter --strength 0.4 --out <run>/merged-0.4
"""
import argparse
import torch
from peft import PeftModel
from peft.tuners.lora import LoraLayer
from transformers import AutoProcessor, Nemotron3_5AsrForRNNT
from train_lora import MODEL, REVISION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter', required=True)
    parser.add_argument('--strength', type=float, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    base = Nemotron3_5AsrForRNNT.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32)
    model = PeftModel.from_pretrained(base, args.adapter)
    for module in model.modules():
        if isinstance(module, LoraLayer):
            for adapter in module.scaling:
                module.scaling[adapter] *= args.strength
    model.merge_and_unload().save_pretrained(args.out)
    AutoProcessor.from_pretrained(MODEL, revision=REVISION).save_pretrained(args.out)
    print(f'adapter at strength {args.strength} merged into {args.out}')


if __name__ == '__main__':
    main()

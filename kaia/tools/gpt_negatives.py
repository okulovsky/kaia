import argparse
from brainbox import BrainBox
from chara.common import CharaApis
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder
from chara.paraphrasing.negatives import (
    NegativeCase, NegativePrompter,
    NegativePipeline, NegativePipelineCache,
)
from foundation_kaia.misc import Loc

MODEL = 'llama3.1:8b'


def main():
    parser = argparse.ArgumentParser(description='Generate negative (anti-)dataset of kitchen chatter phrases')
    parser.add_argument('--target', type=int, default=200, help='Target number of negative phrases')
    parser.add_argument('--phrases-per-batch', type=int, default=20, help='Phrases requested per LLM call')
    parser.add_argument('--languages', nargs='+', default=['ru'], help='Languages to generate for')
    parser.add_argument('--model', default=MODEL, help='Ollama model name')
    parser.add_argument('--output', default=None, help='Output text file path')
    parser.add_argument('--brainbox', default='127.0.0.1:8090', help='BrainBox API address')
    args = parser.parse_args()

    CharaApis.brainbox_api = BrainBox.Api(args.brainbox)

    n_batches_per_lang = max(1, (args.target + args.phrases_per_batch - 1) // args.phrases_per_batch)
    cases = [
        NegativeCase(language=lang, batch_index=i)
        for lang in args.languages
        for i in range(n_batches_per_lang)
    ]

    builder = PromptTaskBuilder(
        prompter=NegativePrompter(n_phrases=args.phrases_per_batch),
        model=args.model,
    )
    cache = NegativePipelineCache(Loc.data_folder / 'negatives_cache')
    NegativePipeline(builder)(cache, cases)

    phrases = cache.read_result()
    output = args.output or (Loc.data_folder / 'negatives.txt')
    from pathlib import Path
    Path(output).write_text('\n'.join(phrases), encoding='utf-8')
    print(f"Done. {len(phrases)} negative phrases → {output}")


if __name__ == '__main__':
    main()

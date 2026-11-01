"""
The speech recognition systems of Kaia side by side on the phrases of build_dataset.py words, through BrainBox as Kaia runs them.
It works in the environment of Kaia. The results of each system are in <out>/<system>.jsonl, a stopped run continues.

    python chara/nlu/nemotron_tuning/compare.py --manifest <data>/words-test.jsonl --dataset <folder>/dataset.json --out <run>

--dataset is the corpus of KenLM, the same dataset.json as the NLU is trained on.
"""
import argparse
import json
import sys
import time
import wave
from pathlib import Path
from avatar.daemon import StreamingSTTService
from brainbox.deciders import Nemotron, WhisperKenLM
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc
from chara.nlu.kenlm_training import KenLMTrainingPipeline
from kaia.app import KaiaAppSettings

sys.path.insert(0, str(Path(__file__).parent))
import manifest  # noqa: E402
import metrics  # noqa: E402

WORKING_FOLDER = Loc.data_folder/'nemotron-tuning'
LANGUAGES = ('en', 'de', 'ru')
CHUNK_SIZE = 7056


def nemotron_chunks(data: bytes) -> list[bytes]:
    return [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]


def nemotron_auto(api, data: bytes, name: str, model: str | None) -> str:
    result = api.execute(Nemotron.new_task().transcribe_stream(nemotron_chunks(data), language='auto', model=model))
    return StreamingSTTService.read_final_text(api.cache.read_file(result).content)


def nemotron_languages(api, data: bytes, name: str, model: str | None) -> str:
    result = api.execute(Nemotron.new_task().transcribe_stream_languages(nemotron_chunks(data), languages=list(LANGUAGES), model=model))
    streams = StreamingSTTService.read_finals_by_stream(api.cache.read_file(result).content)
    return StreamingSTTService.choose_text(streams, LANGUAGES)


def whisper(weight: float):
    def transcribe(api, data: bytes, name: str, model: str | None) -> str:
        api.cache.upload(name, data)
        return api.execute(WhisperKenLM.new_task().transcribe(name, weight=weight, languages=list(LANGUAGES)))
    return transcribe


SYSTEMS = {
    'whisper': whisper(0),
    'whisper-kenlm': whisper(0.5),
    'nemotron-auto': nemotron_auto,
    'nemotron-languages': nemotron_languages,
}


def duration(data_path: str) -> float:
    with wave.open(data_path) as w:
        return w.getnframes() / w.getframerate()


def run(api, system: str, items: list[dict], out: Path, model: str | None) -> list[dict]:
    path = out/f'{system}.jsonl'
    done = {}
    if path.is_file():
        done = {r['audio']: r for r in map(json.loads, path.read_text().splitlines())}
    with open(path, 'a') as file:
        for index, item in enumerate(items):
            if item['audio'] in done:
                continue
            data = Path(item['audio']).read_bytes()
            begin = time.perf_counter()
            hypothesis = SYSTEMS[system](api, data, f'compare-{Path(item["audio"]).name}', model)
            row = dict(item, hypothesis=hypothesis, seconds=time.perf_counter() - begin)
            done[item['audio']] = row
            file.write(json.dumps(row, ensure_ascii=False) + '\n')
            file.flush()
            if (index + 1) % 50 == 0:
                print(f'{system}: {index + 1}/{len(items)}', flush=True)
    return [done[i['audio']] for i in items]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--dataset', required=True, help='dataset.json: the corpus of KenLM')
    parser.add_argument('--out', required=True)
    parser.add_argument('--systems', nargs='+', default=list(SYSTEMS), choices=list(SYSTEMS))
    parser.add_argument('--nemotron-model', default=None, help='a model of installation.yaml, e.g. the tuned one')
    args = parser.parse_args()

    items = manifest.read(args.manifest)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    total = sum(duration(i['audio']) for i in items)

    settings = KaiaAppSettings()
    settings.kaia = None
    settings.avatar_server = None
    settings.avatar_processor = None
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    app = settings.create_app(WORKING_FOLDER)
    with Fork(app.brainbox_server):
        api = app.brainbox_api
        api.wait_for_connection(30)
        if any(s.startswith('whisper') for s in args.systems):
            texts = [r['text'] for r in json.loads(Path(args.dataset).read_text())]
            api.execute(WhisperKenLM.new_task().train_lm(KenLMTrainingPipeline.corpus(texts)))
        reports = []
        for system in args.systems:
            rows = run(api, system, items, out, args.nemotron_model)
            rtf = sum(r['seconds'] for r in rows) / total
            lines = [f'{system}: {len(rows)} phrases, {total:.0f} s of audio, RTF {rtf:.2f}'] + metrics.table(rows)
            reports.extend(lines + [''])
            print('\n'.join(lines), flush=True)
    (out/'report.txt').write_text('\n'.join(reports))


if __name__ == '__main__':
    main()

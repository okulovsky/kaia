"""
Builds the speech datasets for the fine-tuning of Nemotron, in the environment of Kaia (it needs BrainBox and Docker).

    # The texts of the NLU dataset voiced by many Piper speakers: <out>/train.jsonl, <out>/dev.jsonl and <out>/wavs
    python chara/nlu/nemotron_tuning/build_dataset.py tts --dataset <folder>/dataset.json --out <out>

    # Phrases with made-up words: <out>/words-test.jsonl, and <out>/words-train.jsonl with --train-per-language
    python chara/nlu/nemotron_tuning/build_dataset.py words --dataset <folder>/dataset.json --out <out>

    # Recordings of real voices as the test set: <out>/real.jsonl and <out>/real
    python chara/nlu/nemotron_tuning/build_dataset.py real --labels labels.json --audio-dir <folder> --out <out>

The dev set has both the texts and the speakers that are not in the training set.
Russian has only four Piper voices: add real recordings or cloned voices for it, see README.md.
"""
import argparse
import json
import random
import shutil
import sys
from pathlib import Path
import requests
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc
from brainbox.deciders import Piper
from brainbox.deciders.voice_generation.piper.app.model import PiperModelSpec
from brainbox.framework import BrainBoxSetup
from kaia.app import KaiaAppSettings

sys.path.insert(0, str(Path(__file__).parent))
import manifest  # noqa: E402
import words as made_up  # noqa: E402

PIPER_VOICES = 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/'
# Checked on ordinary phrases: Nemotron does not understand de_DE-mls and de_DE-ramona, and thorsten_emotional has
# whispering and drunk speakers. Multi-speaker voices give the variety; l2arctic is English with foreign accents.
VOICES = {
    'en': ['en_US-libritts_r-medium', 'en_GB-vctk-medium', 'en_US-arctic-medium', 'en_US-l2arctic-medium', 'en_US-lessac-medium',
           'en_US-amy-medium', 'en_US-kristin-medium', 'en_GB-alan-medium', 'en_US-ryan-medium'],
    'de': ['de_DE-thorsten-high', 'de_DE-thorsten-medium', 'de_DE-karlsson-low', 'de_DE-eva_k-x_low', 'de_DE-pavoque-low', 'de_DE-kerstin-low'],
    'ru': ['ru_RU-irina-medium', 'ru_RU-ruslan-medium', 'ru_RU-denis-medium', 'ru_RU-dmitri-medium'],
}
# Never in the training set. Thorsten is the same person in both voices
TEST_VOICES = {
    'en': ['en_US-lessac-medium', 'en_US-amy-medium', 'en_GB-alan-medium', 'en_US-ryan-medium'],
    'de': ['de_DE-thorsten-high', 'de_DE-thorsten-medium', 'de_DE-karlsson-low', 'de_DE-eva_k-x_low'],
    'ru': ['ru_RU-irina-medium', 'ru_RU-ruslan-medium'],
}
WORKING_FOLDER = Loc.data_folder/'nemotron-tuning'
BATCH = 32


def piper_catalog() -> dict:
    reply = requests.get(PIPER_VOICES + 'voices.json', timeout=60)
    reply.raise_for_status()
    return reply.json()


def speakers(catalog: dict, language: str, per_voice: int, rnd: random.Random) -> list[tuple[str, int | None]]:
    """(voice, speaker) pairs: a sample of the speakers of each multi-speaker voice"""
    result = []
    for voice in VOICES[language]:
        count = catalog[voice]['num_speakers']
        if count == 1:
            result.append((voice, None))
        else:
            result.extend((voice, s) for s in sorted(rnd.sample(range(count), min(per_voice, count))))
    return result


def spec(catalog: dict, voice: str) -> PiperModelSpec:
    files = catalog[voice]['files']
    model = next(f for f in files if f.endswith('.onnx'))
    return PiperModelSpec(config_url=PIPER_VOICES + model + '.json', url=PIPER_VOICES + model)


def split(items: list, dev_share: float, rnd: random.Random) -> tuple[list, list]:
    items = list(items)
    rnd.shuffle(items)
    dev_count = int(round(len(items) * dev_share)) if len(items) >= 5 else 0
    return items[dev_count:], items[:dev_count]


def plan(texts_by_language: dict, catalog: dict, args, rnd: random.Random) -> list[dict]:
    jobs = []
    for language, texts in texts_by_language.items():
        train_texts, dev_texts = split(sorted(texts), args.dev_share, rnd)
        train_speakers, dev_speakers = split(speakers(catalog, language, args.speakers_per_voice, rnd), args.dev_share, rnd)
        # With too few speakers to hold any out, the dev set differs from the training set only in the texts
        dev_speakers = dev_speakers or train_speakers
        for part, part_texts, part_speakers in (('train', train_texts, train_speakers), ('dev', dev_texts, dev_speakers)):
            for text in part_texts:
                for voice, speaker in rnd.sample(part_speakers, min(args.per_text, len(part_speakers))):
                    jobs.append(dict(part=part, text=text, language=language, voice=voice, speaker=speaker))
    return jobs


def voice_over(jobs: list[dict], catalog: dict, out: Path, part_names: dict[str, str]):
    """Voices the jobs and writes a manifest per part; the fields of a job besides the voice go to its record"""
    (out/'wavs').mkdir(parents=True, exist_ok=True)
    settings = KaiaAppSettings()
    settings.kaia = None
    settings.avatar_server = None
    settings.avatar_processor = None
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    app = settings.create_app(WORKING_FOLDER)
    with Fork(app.brainbox_server):
        api = app.brainbox_api
        api.wait_for_connection(30)
        BrainBoxSetup().up(Piper).execute(api)
        for voice in sorted({j['voice'] for j in jobs}):
            print('Installing the voice', voice)
            api.execute(Piper.new_task().download_model(voice, spec(catalog, voice)))
        records = {part: [] for part in part_names}
        for start in range(0, len(jobs), BATCH):
            batch = jobs[start:start + BATCH]
            results = api.execute([Piper.new_task().voiceover(j['text'], model=j['voice'], speaker=j['speaker']) for j in batch])
            for index, (job, result) in enumerate(zip(batch, results)):
                name = f'{job["part"]}-{start + index:06d}.wav'
                (out/'wavs'/name).write_bytes(api.cache.read_file(result).content)
                extra = {k: v for k, v in job.items() if k not in ('part', 'text', 'language', 'voice', 'speaker')}
                records[job['part']].append(dict(
                    audio=f'wavs/{name}', text=job['text'], language=manifest.LOCALES[job['language']],
                    voice=job['voice'] if job['speaker'] is None else f'{job["voice"]}#{job["speaker"]}',
                    **extra,
                ))
            print(f'{min(start + BATCH, len(jobs))}/{len(jobs)}', flush=True)
    for part, file_name in part_names.items():
        manifest.write(out/file_name, records[part])
        print(part, len(records[part]), 'utterances in', out/file_name)


def tts(args):
    rnd = random.Random(args.seed)
    texts_by_language = {}
    for path in args.dataset:
        for record in json.loads(Path(path).read_text()):
            if record['language'] in VOICES:
                texts_by_language.setdefault(record['language'], set()).add(manifest.as_model_writes(record['text']))
    if args.limit is not None:
        texts_by_language = {l: set(rnd.sample(sorted(t), min(args.limit, len(t)))) for l, t in texts_by_language.items()}
    catalog = piper_catalog()
    jobs = plan(texts_by_language, catalog, args, rnd)
    print(f'{len(jobs)} utterances: ' + ', '.join(f'{l} {sum(j["language"] == l for j in jobs)}' for l in texts_by_language))

    voice_over(jobs, catalog, Path(args.out), dict(train='train.jsonl', dev='dev.jsonl'))


def words(args):
    """The test words and speakers are never in the training set, so the test measures hearing and not memory"""
    rnd = random.Random(args.seed)
    known = {w.lower() for path in args.dataset for r in json.loads(Path(path).read_text()) for w in manifest.normalize(r['text']).split()}
    catalog = piper_catalog()
    jobs = []
    for language in made_up.LANGUAGES:
        all_speakers = speakers(catalog, language, args.speakers_per_voice, rnd)
        many = [s for s in all_speakers if s[1] is not None]
        test_speakers = [s for s in all_speakers if s[0] in TEST_VOICES[language]]
        test_speakers += rnd.sample(many, int(len(many) * args.test_speakers_share))
        train_speakers = [s for s in all_speakers if s not in test_speakers]
        test = [p for group in made_up.GROUPS for p in made_up.phrases(language, group, args.test_per_group, rnd, known)]
        train = made_up.phrases(language, 'new', args.train_per_language, rnd, known)
        for part, part_phrases, part_speakers in (('test', test, test_speakers), ('train', train, train_speakers)):
            for phrase in part_phrases:
                voice, speaker = rnd.choice(part_speakers)
                text = manifest.as_model_writes(phrase['text'])
                jobs.append(dict(phrase, part=part, text=text, voice=voice, speaker=speaker))
    print(f'{len(jobs)} utterances, test ' + str(sum(j['part'] == 'test' for j in jobs)))
    voice_over(jobs, catalog, Path(args.out), {'test': 'words-test.jsonl', 'train': 'words-train.jsonl'})


def real(args):
    """labels.json: [{"file": ..., "language": "ru", "text": ...}], the files are in --audio-dir"""
    out = Path(args.out)
    (out/'real').mkdir(parents=True, exist_ok=True)
    records = []
    for label in json.loads(Path(args.labels).read_text()):
        if not label.get('text') or label.get('language') not in manifest.LOCALES:
            continue
        shutil.copy(Path(args.audio_dir)/label['file'], out/'real'/Path(label['file']).name)
        records.append(dict(audio=f'real/{Path(label["file"]).name}', text=manifest.as_model_writes(label['text']),
                            language=manifest.LOCALES[label['language']]))
    manifest.write(out/'real.jsonl', records)
    print(len(records), 'recordings in', out/'real.jsonl')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('tts')
    p.add_argument('--dataset', action='append', required=True, help='dataset.json of the NLU (text, language), can be repeated')
    p.add_argument('--out', required=True)
    p.add_argument('--per-text', type=int, default=3, help='how many speakers voice each text')
    p.add_argument('--speakers-per-voice', type=int, default=60, help='the speakers taken from a multi-speaker voice')
    p.add_argument('--dev-share', type=float, default=0.1)
    p.add_argument('--limit', type=int, default=None, help='texts per language, for a quick check')
    p.add_argument('--seed', type=int, default=0)
    p = commands.add_parser('words')
    p.add_argument('--dataset', action='append', default=[], help='dataset.json of the NLU: the made-up words are not in its texts')
    p.add_argument('--out', required=True)
    p.add_argument('--test-per-group', type=int, default=100, help='test phrases per language and group (control, names, new)')
    p.add_argument('--train-per-language', type=int, default=0, help='training phrases with made-up words per language')
    p.add_argument('--speakers-per-voice', type=int, default=60)
    p.add_argument('--test-speakers-share', type=float, default=0.2)
    p.add_argument('--seed', type=int, default=0)
    p = commands.add_parser('real')
    p.add_argument('--labels', required=True)
    p.add_argument('--audio-dir', required=True)
    p.add_argument('--out', required=True)
    args = parser.parse_args()
    {'tts': tts, 'words': words, 'real': real}[args.command](args)

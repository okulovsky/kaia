"""
Build a 3-gram KenLM model from text-dataset.json.

Output:
    research/lm/lm.arpa
    research/lm/lm.binary

Usage:
    uv run python research/build_lm.py
"""
import json, subprocess, shutil
from pathlib import Path

DATA   = Path('research/text-dataset.json')
LM_DIR = Path('research/lm')
CORPUS = LM_DIR / 'corpus.txt'
ARPA   = LM_DIR / 'lm.arpa'
BINARY = LM_DIR / 'lm.binary'
ORDER  = 3


def find_bin(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    local = Path.home() / '.local/bin' / name
    if local.exists():
        return str(local)
    raise FileNotFoundError(f'{name} not found — build kenlm from source first')


def main():
    LM_DIR.mkdir(exist_ok=True)

    texts = [d['text'].strip().lower() for d in json.loads(DATA.read_text()) if d.get('text')]
    CORPUS.write_text('\n'.join(texts))
    print(f'Corpus: {len(texts)} sentences → {CORPUS}')

    lmplz       = find_bin('lmplz')
    build_binary = find_bin('build_binary')

    print('Building ARPA...')
    with CORPUS.open() as inp, ARPA.open('w') as out:
        subprocess.run([lmplz, '-o', str(ORDER), '--discount_fallback'],
                       stdin=inp, stdout=out, check=True)
    print(f'ARPA: {ARPA.stat().st_size // 1024}KB')

    print('Building binary...')
    subprocess.run([build_binary, str(ARPA), str(BINARY)], check=True)
    print(f'Binary: {BINARY.stat().st_size // 1024}KB')

    import kenlm
    lm = kenlm.Model(str(BINARY))
    score = lm.score('set a timer for five minutes', bos=True, eos=True)
    print(f'Test score: {score:.3f}')
    print('Done.')


if __name__ == '__main__':
    main()

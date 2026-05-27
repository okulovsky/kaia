import sys, json
from pathlib import Path
from brainbox.deciders import WhisperKenLM

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <wav_file>')
        sys.exit(1)
    wav = Path(sys.argv[1])

    controller = WhisperKenLM.Controller()
    controller.install()

    instance_id = controller.run()
    api = controller.find_api(instance_id)

    texts = [d['text'] for d in json.loads(Path('research/text-dataset.json').read_text())]
    api.train_lm('\n'.join(t.strip().lower() for t in texts if t.strip()))

    result = api.transcribe(wav.read_bytes())
    print(f'file  : {wav.name}')
    print(f'result: {result}')

    controller.stop(instance_id)

# Fine-tuning Nemotron for Kaia's commands

Nemotron 3.5 ASR makes domain errors on Kaia's commands: names ("Col Sakura"), words cut off ("Отмени удильник"),
English said with an accent. These scripts fine-tune it with LoRA on the commands voiced by many TTS speakers,
merge the LoRA into the weights and convert the model to the GGUF of NeMo-Speech.cpp. The runtime and the decider
stay as they are: only the model file changes.

What was measured before (testbed recordings of one real voice, en/de/ru):
- word boosting with the words of the intents does not help reliably: at boost 2 WER goes from 0.212 to 0.182,
  but it inserts words that were not said, and on noisy speech WER grows from 0.673 to 0.837;
- the base model via Transformers transcribes these recordings like the GGUF (similarity 0.913, 21/27 exact);
- the GGUF converted back from the Transformers weights has all 657 tensors identical to the published one.

Expected gain, from the literature on the same kind of data (SLURP, smart home commands):
- NVIDIA, text-only adaptation with a TTS-like generator: WER from 47.1 to 27.7 (41% less) for a LibriSpeech Conformer-L,
  from 23.5 to 15.0 (36% less) for a Conformer-L pretrained on 24k hours ([arXiv 2302.14036](https://arxiv.org/abs/2302.14036), tables 5 and 6);
- Apple, LLM-written texts voiced by TTS: −28% relative WER on average ([arXiv 2309.10707](https://arxiv.org/abs/2309.10707)).

Nemotron is stronger than these base models, so the gain is likely smaller. Fine-tuning on short commands only can
also break general speech: unrestricted fine-tuning on Speech Commands raised LibriSpeech WER from 5.1 to 51%
([arXiv 2210.03255](https://arxiv.org/abs/2210.03255)). Hence LoRA, a low learning rate and general speech in every batch.
NVIDIA's guide to fine-tuning this model with NeMo (full fine-tuning, no LoRA):
[huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr](https://huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr).

## Environments

1. **Kaia** (the repository environment, with Docker): `build_dataset.py`.
2. **Training** (a GPU machine; Python 3.12): `train_lora.py`, `evaluate.py`, `export_gguf.py`.

       python3.12 -m venv .venv-tuning
       .venv-tuning/bin/pip install -r chara/nlu/nemotron_tuning/requirements.txt

   Run the scripts from `chara/nlu/nemotron_tuning`, they import `manifest.py` next to them.
3. **Converter** of NeMo-Speech.cpp, at the commit the decider is built from (4c101bc):

       git clone https://github.com/NVIDIA/NeMo-Speech.cpp && git -C NeMo-Speech.cpp checkout 4c101bc7113f49101a3e11d2c994c519f41939f6
       python3.12 -m venv NeMo-Speech.cpp/.venv && NeMo-Speech.cpp/.venv/bin/pip install -r NeMo-Speech.cpp/requirements.txt

## Data

A manifest is a JSON line per utterance: `{"audio": "wavs/x.wav", "text": "Позвони Сакуре.", "language": "ru-RU"}`,
the audio path relative to the manifest, the text written as Nemotron writes it (a capital letter, final punctuation).

1. **Synthetic commands**: the texts of the NLU dataset (`dataset.json` of `chara/nlu/scripts`) voiced by Piper,
   about 1870 English speakers (LibriTTS, VCTK, L2-ARCTIC with foreign accents), 250 German, but only 4 Russian:

       python chara/nlu/nemotron_tuning/build_dataset.py tts --dataset <folder>/dataset.json --out <data>

   It writes `train.jsonl` and `dev.jsonl`; the dev set has texts and speakers that are not in the training set.
   Russian needs more voices: cloned voices of `chara/voice_clone` or real recordings in the training set.
2. **Real voices, the test set**: record the commands with the testbed (`chara/nlu/testbed/run.py`, the recordings are
   in `data/nlu-testbed/brainbox/cache`) and label them in `labels.json`, `[{"file": ..., "language": "ru", "text": ...}]`:

       python chara/nlu/nemotron_tuning/build_dataset.py real --labels labels.json --audio-dir <folder> --out <data>

   The more speakers and rooms, the better; a few hundred utterances per language make the numbers stable.
3. **General speech**, for `--replay` and for the regression check: a few thousand utterances per language,
   e.g. from FLEURS or Common Voice, as manifests in the same format (texts as the model writes them).

## Steps

1. Baseline:

       python evaluate.py --manifest <data>/real.jsonl --out base-real.json
       python evaluate.py --manifest <general>/test.jsonl --out base-general.json

2. Training. A start:

       python train_lora.py --train <data>/train.jsonl --dev <data>/dev.jsonl --replay <general>/train.jsonl \
           --out <run> --steps 3000 --batch 16 --lr 1e-4 --rank 16 --targets encoder

   - It evaluates the dev set every `--eval-every` steps, keeps the best adapter in `<run>/adapter` and merges it
     into `<run>/merged`; `<run>/log.json` has the loss, the dev WER and the skipped utterances per step.
   - `--targets`: `attention` (the least), `encoder` (attention and feed-forward of the encoder),
     `all` (also the projections, the joint and the language prompt). The LSTM predictor cannot take LoRA.
   - Speed, gain and noise are added on the fly (`--augment`); `--noise-dir` takes recorded noise, e.g. MUSAN.
   - Utterances whose transcript does not fit the audio give a loss of thousands per token and are skipped
     (`--max-loss-per-token`); many skips mean bad data.
   - On the CPU of a laptop a step of 4 utterances takes 5-20 s, so the CPU is only for checking that it runs.

3. The tuned model, on the same sets; the general WER should not grow by more than 0.5-1 point:

       python evaluate.py --manifest <data>/real.jsonl --model <run>/merged --out tuned-real.json
       python evaluate.py --manifest <general>/test.jsonl --model <run>/merged --out tuned-general.json

4. GGUF (it needs about 8 GB of free disk for the temporary .nemo files):

       python export_gguf.py --merged <run>/merged --out <run>/nemotron-tuned.q8_0.gguf \
           --nemo-speech NeMo-Speech.cpp --converter-python NeMo-Speech.cpp/.venv/bin/python

5. In Kaia: put the GGUF into `<brainbox resources>/Nemotron/models/` and add it to `installation.yaml` there,
   next to `multilingual` (sha256 and size of the file, `url` may stay empty):

       multilingual-tuned:
         filename: nemotron-tuned.q8_0.gguf
         rnnt_right_context: 1
         sha256: ...
         size: ...
         url: ''

   Then `StreamingSTTService(..., nemotron_model='multilingual-tuned')` uses it. Check it in the testbed by voice:
   `evaluate.py` decodes offline, while Kaia streams.

## Checking that everything runs

A few minutes on a laptop CPU, with the base model and two training steps. This was run on a Mac:

    python chara/nlu/nemotron_tuning/build_dataset.py tts --dataset <folder>/dataset.json --out <data> --limit 3 --per-text 2 --speakers-per-voice 3
    python chara/nlu/nemotron_tuning/build_dataset.py real --labels labels.json --audio-dir <folder> --out <data>
    head -4 <data>/real.jsonl > <data>/dev_small.jsonl
    python train_lora.py --train <data>/train.jsonl --dev <data>/dev_small.jsonl --out <run> \
        --steps 2 --batch 2 --eval-every 2 --dev-limit 2 --warmup 1 --always-merge --device cpu
    python export_gguf.py --merged <run>/merged --out <run>/tuned.q8_0.gguf --nemo-speech ... --converter-python ...

The GGUF of the two steps differs from the published one in exactly the 192 tensors LoRA was put on (24 layers,
attention and feed-forward) and decodes in the image of the Nemotron decider. Exported from the original weights,
it is identical to the published GGUF.

## Things the scripts work around (Transformers 5.20)

- The processor starts `decoder_input_ids` with its `<blank>` = 13088, outside of the model's vocabulary;
  the model's blank is `config.blank_token_id` = 13087.
- `model(..., labels=...)` falls back to the causal LM loss; the RNN-T loss is computed with torchaudio,
  and it matches an exact computation over the lattice.
- `convert_model.py` reads `.nemo`, so `export_gguf.py` maps the Transformers weights back to NeMo's names
  by their values on the original model.

# Fine-tuning Nemotron to hear any word

The goal, in Yuri's words: how to fine-tune Nemotron so that it recognizes any word. Commands work, but a slot with a word
the model does not know fails: "Позвони Тодороки", "добавь мумзики в список покупок". It breaks the word and the words around it.

These scripts make the test for that, fine-tune Nemotron with LoRA, merge the LoRA into the weights and convert the model to
the GGUF of NeMo-Speech.cpp. The runtime and the decider stay as they are: only the model file changes.

What is measured now, on 900 phrases voiced by Piper with speakers that are checked by ordinary phrases (`build_dataset.py words`,
`compare.py`). The share of phrases with the exact slot word, and in brackets the WER of the words around it:

| System | ordinary word | long name | made-up word |
|---|---|---|---|
| Whisper base | 80.0% (0.137) | 18.3% (0.192) | 6.7% (0.187) |
| Whisper base + KenLM | 80.0% (0.110) | 20.7% (0.170) | 5.7% (0.172) |
| Nemotron, auto | 69.7% (0.172) | 19.7% (0.243) | 6.0% (0.239) |
| Nemotron, 3 languages | 71.0% (0.150) | 21.3% (0.214) | 5.3% (0.224) |
| The same, NeMo-Speech.cpp 1a7e945, regenerated GGUF | 72.3% (0.139) | 21.0% (0.193) | 4.3% (0.207) |

An unknown word raises the errors in the words around it by about a half, in every system, and nobody hears made-up words:
only 4-7% are exact. A made-up word has no single spelling, so `compare.py` also shows the share within 25% of wrong characters.

Earlier results (testbed recordings of one real voice, en/de/ru):
- word boosting with the words of the intents does not help reliably: at boost 2 WER goes from 0.212 to 0.182,
  but it inserts words that were not said, and on noisy speech WER grows from 0.673 to 0.837;
- the base model via Transformers transcribes these recordings like the GGUF (similarity 0.913, 21/27 exact).

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
3. **Converter** of NeMo-Speech.cpp, at the commit the decider is built from (1a7e945):

       git clone https://github.com/NVIDIA/NeMo-Speech.cpp && git -C NeMo-Speech.cpp checkout 1a7e945f3e5553bc51995a1a7ec361ccee3c7280
       python3.12 -m venv NeMo-Speech.cpp/.venv && NeMo-Speech.cpp/.venv/bin/pip install -r NeMo-Speech.cpp/requirements.txt

   The commit matters: since 1a7e945 the converter keeps the pointwise convolutions in F16, because quantizing them can turn
   speech into long blank runs. The GGUF published on Hugging Face in September is older, and a new runtime does not repair it.

## Data

A manifest is a JSON line per utterance: `{"audio": "wavs/x.wav", "text": "Позвони Сакуре.", "language": "ru-RU"}`,
the audio path relative to the manifest, the text written as Nemotron writes it (a capital letter, final punctuation).

1. **Made-up words**, `words.py`: carriers of four skills (call, meeting, shopping, room) with a word in the slot. The test has three
   groups: `control` with ordinary words, `names` with the long names of the testbed, `new` with made-up words.

       # The test set: 100 phrases per language and group
       python chara/nlu/nemotron_tuning/build_dataset.py words --dataset <folder>/dataset.json --out <test>
       # The training set: nothing from the test, neither words nor speakers
       python chara/nlu/nemotron_tuning/build_dataset.py words --dataset <folder>/dataset.json --hold-out <test>/words-test.jsonl \
           --out <data> --test-per-group 0 --train-per-language 5000 --train-ordinary 1000

   It writes `words-test.jsonl`, `words-train.jsonl` and `words-ordinary.jsonl` (phrases of the dataset without names, for `--replay`).
   Voices are checked on ordinary phrases, see `VOICES` in `build_dataset.py`: `de_DE-mls` is not understood at all. There are few good
   voices: Russian has 4 and only 2 of them go to training, German has 2 for training. More need cloned voices or real recordings.
2. **Real voices, the test set**: record the commands with the testbed (`chara/nlu/testbed/run_testbed.py`, the recordings are
   in `data/nlu-testbed/brainbox/cache`) and label them in `labels.json`, `[{"file": ..., "language": "ru", "text": ...}]`:

       python chara/nlu/nemotron_tuning/build_dataset.py real --labels labels.json --audio-dir <folder> --out <data>

   The more speakers and rooms, the better; a few hundred utterances per language make the numbers stable.
3. **General speech**, for `--replay` and for the regression check: a few thousand utterances per language,
   e.g. from FLEURS or Common Voice, as manifests in the same format (texts as the model writes them).

## Steps

1. Baseline, in the environment of Kaia, through BrainBox as Kaia runs the systems. The results are in `<run>/report.txt`:

       python chara/nlu/nemotron_tuning/compare.py --manifest <test>/words-test.jsonl --dataset <folder>/dataset.json --out <baseline>

   The general speech and the real voices, in the training environment:

       python evaluate.py --manifest <data>/real.jsonl --out base-real.json
       python evaluate.py --manifest <general>/test.jsonl --out base-general.json

2. Training. A start:

       python train_lora.py --train <data>/words-train.jsonl --dev <test>/words-test.jsonl --replay <data>/words-ordinary.jsonl \
           --replay <general>/train.jsonl --out <run> --steps 3000 --batch 16 --lr 1e-4 --rank 16 --targets encoder

   - It evaluates the dev set every `--eval-every` steps, keeps the best adapter in `<run>/adapter` and merges it
     into `<run>/merged`; `<run>/log.json` has the loss, the dev WER and the skipped utterances per step.
   - `--targets`: `attention` (the least), `encoder` (attention and feed-forward of the encoder),
     `all` (also the projections, the joint and the language prompt). The LSTM predictor cannot take LoRA.
   - Speed, gain and noise are added on the fly (`--augment`); `--noise-dir` takes recorded noise, e.g. MUSAN.
   - The loss starts at about 1 per token. An utterance above `--max-loss-per-token` is skipped; many skips mean bad data.
   - On a CPU a step of 4 utterances takes 5-20 s, so a CPU is for a small pilot at most.

3. The tuned model on the same sets. `new` should get better, `control` should not get worse, and the general WER should not
   grow by more than 0.5-1 point. With the slot fields in the manifest `evaluate.py` prints the table of `compare.py`:

       python evaluate.py --manifest <test>/words-test.jsonl --model <run>/merged --out tuned-words.json
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

   Then `StreamingSTTService(..., nemotron_model='multilingual-tuned')` uses it. `evaluate.py` decodes offline, while Kaia streams,
   so the last word is `compare.py --systems nemotron-languages --nemotron-model multilingual-tuned` and the testbed by voice.

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
all its 657 tensors are identical to the direct conversion of the `.nemo` by the same converter.

## Things the scripts work around (Transformers 5.20)

- The labels of the processor do not fit the model. `tokenizer.json` splits the words differently from the SentencePiece
  model the checkpoint was trained with, and the model closes every text with its language tag (`<en-US>`). With these labels
  the loss is 6 per token instead of 1, and the training teaches the splitting, not the words. So the labels are made with
  the SentencePiece model of the `.nemo`, with the tag.
- The config has `layerdrop` 0.1, the checkpoint was trained without it (`stochastic_depth_drop_prob: 0`). A layer is dropped
  for the whole batch, and every 6th batch got a loss of thousands. It is turned off.
- The processor starts `decoder_input_ids` with its `<blank>` = 13088, outside of the model's vocabulary;
  the model's blank is `config.blank_token_id` = 13087.
- `model(..., labels=...)` falls back to the causal LM loss; the RNN-T loss is computed with torchaudio,
  and it matches an exact computation over the lattice.
- `convert_model.py` reads `.nemo`, so `export_gguf.py` maps the Transformers weights back to NeMo's names
  by their values on the original model.

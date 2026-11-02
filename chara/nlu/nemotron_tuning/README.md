# Fine-tuning Nemotron to hear any word

The goal, in Yuri's words: how to fine-tune Nemotron so that it recognizes any word. Commands work, but a slot with a word
the model does not know fails: "Позвони Тодороки", "добавь мумзики в список покупок". It breaks the word and the words around it.

These scripts make the test for that, fine-tune Nemotron with LoRA, merge the LoRA into the weights and convert the model to
the GGUF of NeMo-Speech.cpp. The runtime and the decider stay as they are: only the model file changes.

## Results

Six systems on the same sets, run as Kaia runs them: Whisper through BrainBox, Nemotron streaming in the image of the decider
with 3 language streams (en, de, ru) and `StreamingSTTService.choose_text`.
- Nemotron: NeMo-Speech.cpp 1a7e945 and the GGUF converted there.
- Nemotron tuned: the pilot below, merged at strength 0.4.
- KenLM: for Whisper the LM of its decider, for Nemotron a token LM of the testbed dataset at weight 0.2 in the decoder
  (`train_token_lm.py` and the patch of the decider).

| System | Made-up word | Long name | Ordinary word | FLEURS WER, 3 streams / right language | Real commands | Lag, s |
|---|---|---|---|---|---|---|
| Whisper base | 6.7 / 34.4 | 15.6 / 50.0 | 65.6 / 73.3 | 0.151 | 40 | 2.11 |
| Whisper base + KenLM | 6.7 / 34.4 | 14.4 / 51.1 | 66.7 / 74.4 | 0.154 | 43 | 2.06 |
| Nemotron | 4.4 / 28.9 | 18.9 / 43.3 | 64.4 / 74.4 | 0.131 / 0.123 | 48 | 0.57 |
| Nemotron + KenLM | 2.2 / 26.7 | 24.4 / 47.8 | 64.4 / 74.4 | - / 0.133 | 51 | 0.53 |
| Nemotron tuned | 13.3 / 48.9 | 22.2 / 53.3 | 73.3 / 83.3 | 0.125 / 0.123 | 56 | 0.57 |
| Nemotron tuned + KenLM | 7.8 / 48.9 | 32.2 / 57.8 | 75.6 / 83.3 | - / 0.136 | 55 | 0.56 |

- The slot columns: the share of phrases with the slot word exact / within 25% of wrong characters, of 90 phrases each,
  voiced by Piper in carriers the training never saw (`words-unseen.jsonl`). A made-up word has no single spelling, hence the second number.
- FLEURS: WER on 300 clips of real read speech, 100 per language. Nemotron with 3 streams as in Kaia, and with the stream
  of the right language only; the LM was run with the right language only. Whisper chooses the language itself.
- Real commands: exact, of the 77 testbed recordings with speech.
- Lag: the median time from the end of a phrase to its text, for 27 real recordings that arrive in real time, on 4 CPU cores.
  Whisper does not stream, its text comes after the phrase: this is the median time of one of the 77 recordings through BrainBox.

What follows:
- Tuning makes Nemotron hear an unknown word as a word. In the new carriers, against Nemotron it is better on 50 phrases
  with made-up words and worse on 10, against Whisper better on 50 and worse on 25. General speech, real commands and speed
  do not get worse.
- The exact spelling of an unknown word stays rare, because the sound does not define it. In the 14 test phrases with "Тодороки"
  Nemotron breaks the name or joins it with the neighbours ("встречу ста дороки") and writes it as one word once, the tuned model
  writes one word that sounds right in 10 ("встречу с Тадороки"), and neither writes "Тодороки". So the NLU should compare slot values loosely.
- KenLM helps only the words it has seen. With the tuned model, the long names of the testbed gain (exact 22.2% to 32.2%,
  "Тодороки" in 4 of the 14 phrases), made-up words lose (13.3% to 7.8%), and FLEURS loses about 1 point of WER.
  It suits words known in advance, such as contacts.
- In the carriers of the training (900 phrases of `words-test.jsonl`) the tuned model has exact / close of 8.0 / 40.7 for made-up
  words, 24.3 / 56.3 for long names and 80.7 / 85.7 for ordinary words, against 4.3 / 24.7, 21.0 / 42.7 and 72.3 / 78.7 of Nemotron.
  Part of that gain is the memory of the carriers, so choose a model by the new carriers.

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
([arXiv 2210.03255](https://arxiv.org/abs/2210.03255)). Hence LoRA, a low learning rate and real speech in the training.
NVIDIA's guide to fine-tuning this model with NeMo (full fine-tuning, no LoRA):
[huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr](https://huggingface.co/blog/nvidia/fine-tuning-nemotron-35-asr).

## What a pilot on a CPU showed

A pilot on 4 CPU cores, so the data is small: 3600 phrases with made-up words and 900 ordinary phrases voiced by Piper, `--targets all`,
rank 16, batch 4, lr 1e-4, the best of 1500 steps was 900. All numbers are of the GGUF in the runtime, streaming with 3 language streams;
FLEURS has only the stream of the right language.

| Model | FLEURS WER | Rare words | Real commands | Ordinary word | Long name | Made-up word |
|---|---|---|---|---|---|---|
| Base | 0.123 | 86.8% | 48 | 74.4% | 43.3% | 28.9% |
| Piper only, strength 1 | 0.220 | 70.7% | 56 | 80.0% | 48.9% | 63.3% |
| Piper only, strength 0.4 | 0.123 | 84.8% | 56 | 83.3% | 53.3% | 48.9% |
| Piper and real speech, strength 1 | 0.127 | 84.5% | 51 | 83.3% | 54.4% | 52.2% |

- FLEURS: 300 clips of real speech, 100 per language.
- Rare words: 355 words of 5 letters and more from these clips, `wordfreq` zipf below 3, the share within 25% of wrong characters.
- Real commands: exact, of the 77 testbed recordings with speech.
- The last three columns: the share within 25% of wrong characters on 270 Piper phrases in carriers the training never saw (`words-unseen.jsonl`).

What follows from it:

- A run that looks good can break real speech. Piper only at strength 1 took FLEURS from 0.123 to 0.220, and worse on 203 of the 300 clips,
  while the real commands did not show it (61 to 62 of 77 with similarity at least 0.8). So FLEURS is a required check.
- The harm grows faster than the gain, so an adapter can be merged at a lower strength without training again (`merge_lora.py`).
  On dev (90 real clips and 90 phrases), for strength 0, 0.25, 0.4, 0.5 and 1, the WER of real speech is 0.090, 0.090, 0.091, 0.103, 0.199,
  and the WER of the phrases is 0.272, 0.220, 0.196, 0.181, 0.142.
  The harm comes from the encoder layers of the adapter: with only them the real speech has 0.177, with only the projections and the joint 0.087.
- Real speech in the training protects real speech: half of the steps from FLEURS (1369 clips up to 8 s, batch 2) gave 0.127 at strength 1.
  The price is fewer steps on Piper: on 300 ordinary phrases in new voices its WER is 0.193, at strength 0.4 it is 0.138, the base model has 0.208.
  In Russian it also started to write numbers as digits, in 24 of the 100 phrases against 1 of the base model: 182 of the 1369 clips have digits
  in their texts. Leave such clips out of `--replay`.
- The carriers of `words-test.jsonl` are in the training set, so that test also measures memory. Long names at strength 1 have 56.0% close and
  a neighbour WER of 0.050 there, and 48.9% and 0.213 in unseen carriers, where the base model has 43.3% and 0.154. Choose by `words-unseen.jsonl`.
- All phrases with made-up words are voiced by Piper. The base model has WER 0.208 on ordinary phrases in these voices and 0.123 on FLEURS,
  so the numbers of made-up words on real voices are unknown.

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
       # The second test, in carriers the training never sees: 30 phrases per language and group
       python chara/nlu/nemotron_tuning/build_dataset.py words --dataset <folder>/dataset.json --hold-out <data>/words-train.jsonl \
           --out <unseen> --test-per-group 0 --unseen-per-group 30

   It writes `words-test.jsonl`, `words-unseen.jsonl`, `words-train.jsonl` and `words-ordinary.jsonl` (phrases of the dataset without names).
   Voices are checked on ordinary phrases, see `VOICES` in `build_dataset.py`: `de_DE-mls` is not understood at all. There are few good
   voices: Russian has 4 and only 2 of them go to training, German has 2 for training. More need cloned voices or real recordings.
2. **Real voices, the test set**: record the commands with the testbed (`chara/nlu/testbed/run_testbed.py`, the recordings are
   in `data/nlu-testbed/brainbox/cache`) and label them in `labels.json`, `[{"file": ..., "language": "ru", "text": ...}]`:

       python chara/nlu/nemotron_tuning/build_dataset.py real --labels labels.json --audio-dir <folder> --out <data>

   The more speakers and rooms, the better; a few hundred utterances per language make the numbers stable.
3. **General speech**, for `--replay` and for the regression check: a few thousand utterances per language,
   as manifests in the same format (texts as the model writes them). The pilot took [FLEURS](https://huggingface.co/datasets/google/fleurs):
   the `train` split for `--replay`, 300 clips of the `validation` split for the check, 90 other clips of it for the dev set.

## Steps

1. Baseline, in the environment of Kaia, through BrainBox as Kaia runs the systems. The results are in `<run>/report.txt`:

       python chara/nlu/nemotron_tuning/compare.py --manifest <test>/words-test.jsonl --dataset <folder>/dataset.json --out <baseline>

   The general speech and the real voices, in the training environment:

       python evaluate.py --manifest <data>/real.jsonl --out base-real.json
       python evaluate.py --manifest <general>/test.jsonl --out base-general.json

2. Training, for a first run:

       python train_lora.py --train <data>/words-train.jsonl --train <data>/words-ordinary.jsonl --replay <general>/train.jsonl \
           --replay-share 0.5 --dev <dev>/words-test.jsonl --out <run> --steps 3000 --batch 16 --lr 1e-4 --rank 16 --targets all

   - It evaluates the dev set every `--eval-every` steps, keeps the best adapter in `<run>/adapter` and merges it
     into `<run>/merged`; `<run>/log.json` has the loss, the dev WER and the skipped utterances per step.
   - The dev set chooses the step, so it needs both phrases and real speech: the pilot had 120 phrases and 90 clips of FLEURS.
     `log.json` has the WER by language and by the `group` of the manifest.
   - A batch comes from one source, `--replay-share` is the share of the steps taken from `--replay`.
     `--replay-batch` makes these batches smaller: real clips are longer and the memory of the loss grows with the length of the clip and of the text.
   - `--targets`: `attention` (the least), `encoder` (attention and feed-forward of the encoder),
     `all` (also the projections, the joint and the language prompt). The LSTM predictor cannot take LoRA.
   - Speed, gain and noise are added on the fly (`--augment`); `--noise-dir` takes recorded noise, e.g. MUSAN.
   - The loss starts at about 1 per token. An utterance above `--max-loss-per-token` is skipped; many skips mean bad data.
   - On a CPU a step of 4 phrases takes 5-20 s, a step of 2 FLEURS clips up to 8 s takes 12 s and about 5 GB, so a CPU is for a small pilot at most.

3. The tuned model on the same sets. `new` should get better, `control` should not get worse, and the general WER should not
   grow by more than 0.5-1 point. With the slot fields in the manifest `evaluate.py` prints the table of `compare.py`:

       python evaluate.py --manifest <unseen>/words-unseen.jsonl --model <run>/merged --out tuned-unseen.json
       python evaluate.py --manifest <test>/words-test.jsonl --model <run>/merged --out tuned-words.json
       python evaluate.py --manifest <data>/real.jsonl --model <run>/merged --out tuned-real.json
       python evaluate.py --manifest <general>/test.jsonl --model <run>/merged --out tuned-general.json

4. If the general WER grew, merge the adapter at a lower strength and evaluate again. Take the highest strength that keeps
   the general WER within the limit:

       python merge_lora.py --adapter <run>/adapter --strength 0.4 --out <run>/merged-0.4

5. GGUF (it needs about 8 GB of free disk for the temporary .nemo files):

       python export_gguf.py --merged <run>/merged --out <run>/nemotron-tuned.q8_0.gguf \
           --nemo-speech NeMo-Speech.cpp --converter-python NeMo-Speech.cpp/.venv/bin/python

6. In Kaia: put the GGUF into `<brainbox resources>/Nemotron/models/` and add it to `installation.yaml` there,
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

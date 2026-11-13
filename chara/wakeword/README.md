# Wake Word Model Training

## Getting started

### 1. Create the wakeword environment

From the repository root:

```sh
conda create -n wakeword --clone brainbox -y
conda activate wakeword
cd chara/wakeword
```

This copies the existing BrainBox environment and its dependencies.

### 2. Set your wake word

In [learn-settings.json](learn-settings.json), set `generation.target_variants` to your word or phrase:

```json
"target_variants": ["computer"]
```

English is currently supported. You can leave the other settings unchanged.

### 3. Start BrainBox

In a separate terminal, from the repository root, activate the `brainbox` environment and start the server:

```sh
conda activate brainbox
python -m brainbox.run --data-folder ./brainbox-data
```

Replace `./brainbox-data` with your existing BrainBox data directory. Keep the server running.

### 4. Get a Hugging Face token

Create a **Read** token in [Hugging Face settings](https://huggingface.co/settings/tokens), then run:

```powershell
conda activate wakeword
huggingface-cli login
```

Paste the token at `Enter your token` and press Enter (input is hidden). Answer `n` when asked to add a Git credential. Then run `make setup`.

### 5. Prepare resources and train

Back in the `wakeword` terminal, from `chara/wakeword`:

```sh
make setup
make check
make run OUTPUT=../../temp/wakeword/my-word-001
```

The first setup downloads models and datasets and requires more than 25 GB of free disk space. Use a new `OUTPUT` directory when training a different wake word.

### 6. Get the results

Open `temp/wakeword/my-word-001/training/` relative to the repository root:

- `wakeword.onnx` — the trained model;
- `report.html` — the training quality report.

## How the pipeline works

1. **Speech generation.** ParlerTTS runs through BrainBox to synthesize the wake word in different voices and similar phrases without it. Vosk verifies and crops the target word from positive recordings.
2. **Data preparation.** Background sounds and room effects are added to the audio. Training and validation recordings are converted into features.
3. **Training.** A classifier learns to distinguish the wake word from similar phrases and background sounds. Speech generation runs in BrainBox; data processing and training run in the `wakeword` environment.
4. **Export and evaluation.** The pipeline selects and averages the best saved model states, exports the model to ONNX, evaluates it, and generates a report.

Generated data is saved to `OUTPUT/generation/`; the model and reports are saved to `OUTPUT/training/`.

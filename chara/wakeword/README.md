# Full wakeword pipeline

Run all commands from the `kaia` project root. Generation and training use the main configuration file, [learn-settings.json](learn-settings.json).

The examples below use PowerShell on Windows. Replace the project and data paths with your own locations.

## 1. Start BrainBox

Start Docker Desktop. In a separate terminal, activate your existing BrainBox environment and start the server from the current project sources:

```powershell
conda activate brainbox
cd D:\Document\FourthCourseMATMEX\kaia
python -m brainbox.run --data-folder "D:\brainbox-data"
```

Keep this terminal open. The client connects to `http://127.0.0.1:8090` by default. If BrainBox runs on another machine, add `--brainbox-url http://SERVER:8090` to the `prepare`, `generate`, and `train` commands.

## 2. Create the environment and prepare resources

Your existing `brainbox` environment must use Python 3.11 or 3.12. In a second terminal, **create a separate `wakeword` environment** by cloning it to reuse the project's base dependencies. Then install the tools and pinned generation dependencies. Changes to `wakeword` do not affect the original `brainbox` environment.

Run these environment creation commands once:

```powershell
conda create --name wakeword --clone brainbox --yes
conda activate wakeword
cd D:\Document\FourthCourseMATMEX\kaia

conda install --channel conda-forge git ffmpeg --yes
python -m pip install --no-deps -r chara/wakeword/requirements-host.lock.txt
python -m pip install --no-deps -e .
```

Run all subsequent commands **in the `wakeword` environment, from the `kaia` project root**. Complete the dependency installation above before starting the pipelines.

```powershell
python -m chara.wakeword.scripts.prepare --scope all
python -m chara.wakeword.scripts.prepare --scope all --check-only
```

The first command prepares ParlerTts, Vosk, the `WakewordTraining` decider, and the required resources. The second checks readiness without installing anything. Wait for a successful readiness check before proceeding.

The initial ACAV download requires internet access and at least 21 GiB of free space on the filesystem containing BrainBox's server resources. Existing prepared and verified background data is reused.

## 3. Set your wakeword

Set your wakeword in `generation.target_variants` in [learn-settings.json](learn-settings.json), and use the same value in `training.expected_target_variants`.

## 4. Generate the dataset

```powershell
python -m chara.wakeword.scripts.generate --config chara/wakeword/learn-settings.json --output temp/wakeword/full-generation-001
```

The output includes the dataset directory, `portable-dataset`, and `dataset.zip`. The archive contains four feature arrays and a manifest. Rejected samples are saved separately in `review`.

## 5. Train the model

Pass the generation output directory from the previous step:

```powershell
python -m chara.wakeword.scripts.train --config chara/wakeword/learn-settings.json --dataset temp/wakeword/full-generation-001 --output temp/wakeword/full-training-001
```

The pipeline validates the dataset and uploads the archive through the BrainBox API. Training runs inside the `WakewordTraining` container, using the permanent ACAV background stored in the server's resources.

After successful completion, `temp/wakeword/full-training-001` contains:

- `wakeword.onnx`: the trained model, if `training.model_name` retains its default value;
- `report.html` and `report_ru.html`: the English and Russian reports;
- `metrics.json`, training history, saved validation scores, and dataset metadata.

Use new output directories when changing settings, for example by replacing the `001` suffix with `002`.

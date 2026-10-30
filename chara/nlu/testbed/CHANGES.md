# NLU testbed: what was changed to make it work

Commits e5f6dc63c..5bf28c15e on `ultimate_nlu_testing`.

## 1. OptionsDub values: no expanding, no translation of the keys

- `enable_options_expanding=False` in `TextDatasetPipeline` (e5f6dc63c). Paraphrasing no longer invents new options
  ("Маме" for a `person` that is Yuki/Sakura).
- Everything that existed only to clean up after the expanding is removed (397dae466):
  - `_CLOSED_OPTIONS` / `_CLOSED_OPTIONS_INDEX` in `ner_training/dataset.py`: the hand-written lists of "Tomorrow",
    "Morgen früh", "Завтра утром"... and the dropping of records whose value was not in the list;
  - in `TextDatasetPipeline.export`, the fallback "if the value is not in the original options, keep the said form".
    Now it is just `original_options.get(variable.name, variable.dub)`;
  - the expanded option in `test_text_dataset.py`.
- `enable_option_values_translation=False` (30dd948fb). With it on, `OptionHeaderLocation` renamed the keys
  of the options, so `dataset.json` had translated values ("Kirschblüte") instead of the template's ones.
  The said forms are still translated by `OptionLocation`, only the keys stay.

Result: in `dataset.json` every OptionsDub value is a key of the original template, whatever the language of the text.

## 2. Every OptionsDub value is trained at least once

`NerTrainingPipeline._samples` caps each intent at `samples_per_intent`, so rare values could be cut away (f33a329ab).

- Each training record now carries the set of its `(name, value)` OptionsDub pairs.
- `_take_covering_options`: after the shuffle, the samples that bring a new value come first, then the others
  up to the limit. If there are more values than the limit, the limit is exceeded.
- Test: `test_all_options_are_trained`.

This is done in NER training, not in the export of `dataset.json`: the dataset has plenty of paraphrases
per template and mood, the cap is applied only when the training samples are chosen.

## 3. Training does not deploy

`NerTrainingPipeline` used to upload the adapter to `LlamaLoraServer` as the last phase (af99e662a).

- The phase `deployment` → `adapter`: it only writes `nlu-slots.gguf` of the best checkpoint into the run folder.
- `NerTrainingReport.deployed_checkpoint` → `best_checkpoint`.
- Test: `test_best_checkpoint_is_deployed` → `test_best_checkpoint_is_saved`.
- Deployment is only in `deploy_ultimate_nlu`, called by the testbed.

The rename breaks the cached `result.json` of the older trainings (SerializationMismatch on `best_checkpoint`),
so the trainings made before af99e662a must be retrained.

Note: KenLM and Chroma are trained in place on the deciders, so `train_ultimate_nlu` still changes them
on the BrainBox it runs against. Only the NER adapter is deployed separately.

## 4. Scripts, without arguments

Removed: `run.py` with argument parsing, `run_dataset.py`, `run_negatives.py` (0b50eac15, cba441715). Now:

- `training.py`: `create_dataset`, `create_negatives` (commented out, they are run only when the data should grow)
  and `train_ultimate_nlu` on `kaia-content/nlu_testbed`. Uses the research BrainBox, does not start its own.
- `run_inference_brainbox.py`: starts the inference BrainBox.
- `run_testbed.py`: deploys the models and runs the testbed app.

`create_dataset` tops up: `CasePrioritization` with `only_new` takes only template × language × mood
missing in the finished runs. `create_negatives` does not: each call is a new run of `batches_per_language`
batches per language, `negatives.txt` is rebuilt from all the runs with duplicates removed.
Both rebuild the files, which changes the hash of `$training/<hash>`, so the next training is from scratch.

## 5. Research BrainBox ≠ inference BrainBox

The testbed needs many deciders up at once (Nemotron, WhisperKenLM, Chroma, LlamaLoraServer),
the research BrainBox does not run them in parallel. A BrainBox inside the testbed process resets the deciders
at every start. So (a12fdead7, 5bf28c15e):

- `run_inference_brainbox(working_folder)` in `app/app.py`: a separate long-lived process with `AlwaysOnPlanner`,
  `stop_controllers_at_termination=False`, on the same port 8090 as the research one, so only one can run.
  Models are shared with the research BrainBox (no redownloading); cache, database and self-tests are
  in `data/nlu-testbed/brainbox`.
- `run_nlu_testbed`:
  1. points the app to `http://127.0.0.1:8090` and the cache `data/nlu-testbed/brainbox/cache`;
     `settings.brainbox=None`, it never starts a BrainBox;
  2. `_check_inference_brainbox`: fails if nothing answers the heartbeat, then writes a probe file into the cache
     and fails if the BrainBox does not see it. The avatar and the BrainBox exchange the recordings
     as local files of the cache, so it must be the same folder; otherwise it is probably the research BrainBox;
  3. `set_up_deciders`;
  4. `deploy_models=True` (default): `deploy_ultimate_nlu`. With `False`, whatever was deployed the last time is
     evaluated, at the caller's risk;
  5. frontend, avatar fork, browser.
- `testbed_deciders` lost the `ollama` flag.

## Order of work

1. Research BrainBox up → `training.py`.
2. Research BrainBox down → `run_inference_brainbox.py`.
3. `run_testbed.py`.

## Open

- Texts of `dataset.json`: in de/ru the option values are not declined ("в кухня", "Позвони сакура", "im Küche"),
  grammar correction does not reach the option values.
- `export` draws number/option values at random without a seed, so rebuilding `dataset.json` without new runs
  still changes it and the training hash.
- `BrainBoxSetup.execute` calls `load_model` on every testbed start, Nemotron is reloaded each time.
- `test_testbed`: `test_report_is_shown_in_chat`, `test_typed_text_comes_before_its_report` fail,
  also before these changes.

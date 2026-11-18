> Уточнение архитектуры 2026-11-18: оркестрация — chara/wakeword/generation_pipeline.py и training_pipeline.py; обучение внутри контейнера — brainbox/deciders/voice_analysis/wakeword_training/runtime. Исторические пути ниже заменены этим разделением.

﻿# Contracts: Python pipelines and migration

Paths в командах разрешаются относительно cwd, JSON-relative paths — относительно JSON. Команды реализованы; результаты приёмки и внешние ограничения см. в validation.md.

## Entry points

Из корня kaia, в установленном проектном окружении:

- `python -m chara.wakeword.scripts.prepare --config chara/wakeword/learn-settings.json --scope generation|training|all --brainbox-url URL [--check-only]`
- `python -m chara.wakeword.scripts.generate --config chara/wakeword/learn-settings.json --output HOST_GENERATION_OUTPUT --brainbox-url URL`
- `python -m chara.wakeword.scripts.train --config chara/wakeword/learn-settings.json --dataset HOST_GENERATION_OUTPUT --output HOST_TRAINING_OUTPUT --brainbox-url URL`
- `python -m chara.wakeword.scripts.report --output HOST_TRAINING_OUTPUT`

prepare --check-only читает состояния и ничего не устанавливает; без флага выполняет явную подготовку. Generation scope проверяет Parler/Vosk и локальные аудиоресурсы. Training scope проверяет WakewordTraining и его серверный resource profile; не устанавливает local torch/ORT/FMA/FFmpeg. All объединяет, сервер недоступен -> инструкция запуска BrainBox и ненулевой код. Report scope не обращается к BrainBox и требует только локальный numeric/renderer stack.

`generate` не вызывает trainer. `train` не вызывает Parler/Vosk и не скачивает пропавший фон; предлагает prepare. Makefile удалён. Нельзя молча трактовать прежнюю папку generation как training output. По умолчанию используются full параметры unified config; smoke выбирается явным файлом.

## Library interface

Lazy exports из chara.wakeword: GenerationPipeline, TrainingPipeline, GenerationSettings, TrainingSettings, generate_dataset(settings,output), train_dataset(dataset,settings,expected_dataset,output), render_training_report(output). API подключения берётся через Chara.Apis как в voice_clone. Host training entry point делает Chara.start(output/orchestration), а pipeline.__call__ вызывает именованные стадии; перед Chara cache проверяются content identity/lock. Вспомогательные классы ничего не запускают при импорте.

Generation stages: validate_configuration -> prepare/check_generation_resources -> collect_audio -> normalize/review -> extract_features -> validate_corpus -> package_dataset -> publish_result. Внутренние batch voiceover/recognition/cut сохраняют names и persisted IDs там, где используются существующие outputs.

Training stages: validate_source -> prepare_archive -> check_remote -> persist_request -> submit_or_reconcile -> follow_training -> export_result -> download_result -> verify_result -> publish_result. Получение и обработка ошибок — отдельные методы, __call__ не содержит full DTO сериализацию/архивные циклы/trainer internals.

Return GenerationResult: status, dataset_folder, archive_path/hash, manifest_path/hash, actual original/feature counts, review summary. TrainingResult: status, model/report/report_ru paths, metrics/history/scores/portable marker, remote reference/error_stage/reason.

## Validation ownership

Хост: manifest version, immutable target/expected counts, original lineage counts and split disjointness, safe paths/layout, ZIP CRC/content hashes, NPY header/dimensions/dtype/size и bounded float32 finite scan через stdlib array/struct/math, без torch/ORT/NumPy. Чанки ограничены 262144 значениями, byte order учитывается без изменения исходных файлов. Сервер повторяет проверки с NumPy mmap и feature-space/profile compatibility до update. До network submission проверяются integrity и конечность самих файлов (FR-009). Данные слова принимаются по верифицированной metadata, независимый ASR без аудио не выполняется.

## Retry/identity

Persist request/attempt IDs перед отправкой; неизвестный статус API требует reconciliation по прежнему ID. Missing job, finished failure и running различаются. После lost response не создавать новый server training_id. Finished failed attempt с verified training_complete допускает новый persisted job attempt для того же training_id, чтобы завершить оставшиеся server stages; partial optimizer запрещает продолжение. Прежний ошибочный BrainBox job не перезаписывается и не пересылается с дублирующим ID.

Chara cache стадии download не доказывает наличие файлов: verify hashes обязателен после cached result. Если серверные результаты удалены, клиент получает явную ошибку, без скрытого обучения. Уже полностью локальный verified complete переиспользуется без сервера. Параллельный output lock исключает двух писателей.

## Migration

Существующие chara.wakeword generation exports/direct script становятся thin wrappers новых компонентов; без второй копии business logic. Старый host run_training заменяется явно remote wrapper, документация описывает необходимость установленного WakewordTraining. Legacy full API может делегировать двум новым пайплайнам, но не сохраняет третий отдельный trainer. Старые feature001/002 outputs не переписываются; compatible legacy generation manifest адаптируется в portable ZIP, incompatible требует новую генерацию с причиной.

Коды: 0 — complete запрошенной операции; 1 — failed/not ready/incompatible; 2 — ошибка аргументов. Сообщение содержит stage/reason, пути принадлежат соответствующей машине. Проверки Ruff/mypy и поддержка entry points не добавляют зависимости в framework.


## Implementation details and remaining infrastructure constraint

Host training explicitly calls `api.cache.upload(cache_name, dataset_zip)` before creating the job. `dataset` receives the bare cache name, never a client absolute path or database-embedded ZIP bytes. Current `api.add()` does not upload FileLike paths automatically. Upload names are persisted task-specific identities; existing jobs are reconciled before uploading again. Expected corpus_id is checked server-side before updates. Framework functions were not changed.

Portable validation/config/archive imports use stdlib only. Importing existing Chara/Avatar still loads NumPy as a general project dependency. Torch/ORT/ONNX/openwakeword are not imported by the host orchestration. A strictly NumPy-free Chara client is not delivered by this feature: that would require changing the common infrastructure prohibited by the plan. This constraint is explicit rather than hidden by a mocked import test.

The numeric server engine is `brainbox/deciders/voice_analysis/wakeword_training/runtime/execution.py`; remote host orchestration is `chara/wakeword/training_pipeline.py`. Background preparation lives in the decider installer, result packaging in `brainbox/deciders/voice_analysis/wakeword_training/runtime/portable_results.py`; separate background.py/result_export.py adapters would duplicate this small logic.

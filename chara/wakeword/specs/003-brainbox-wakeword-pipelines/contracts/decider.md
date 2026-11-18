> Уточнение архитектуры 2026-11-18: оркестрация — chara/wakeword/generation_pipeline.py и training_pipeline.py; обучение внутри контейнера — brainbox/deciders/voice_analysis/wakeword_training/runtime. Исторические пути ниже заменены этим разделением.

﻿# Contract: WakewordTraining decider

Целевой публичный API нового decider; отдельные HTTP маршруты генерируются существующим marshalling, вручную новые upload endpoints не добавляются.

## Registration, installation, readiness

WakewordTraining экспортируется в brainbox.deciders.voice_analysis и стандартном deciders discovery. DockerMarshallingController предоставляет resource_folder, installer, api и build_image как соседи. Имя образа wakeword_training. app/main.py запускает service через существующую инфраструктуру. Нужна установленная актуальная версия проекта в серверном окружении и перезапуск BrainBox для регистрации нового decider-а; клиентский prepare не подменяет исходники удалённого сервера.

Resource installation: стандартный install / installation.yaml плюс собственный background/manifest.json с source/split/feature-space identities. Источник ACAV закреплён immutable revision/hash в files/resource-profile.json; профиль согласуется с feature extractor generation. Готовятся train/validation подмножества mmap по прежнему split recipe. Неполная загрузка -> temporary, checksum -> publish; installation marker не считается достаточной проверкой готовности. Repair отсутствующих/повреждённых ресурсов — только explicit prepare, не train; несовместимый профиль требует явной установки новой версии без удаления рабочих runs.

Без FMA/MITRIR/Parler/Vosk внутри training image: аудио/аугментации уже обработаны на хосте. Feature-space model hashes нужны как compatibility metadata; файлы extractor моделей не скачиваются, если не используются в training. Runtime locks Linux separate от полного audio lock. Builder копирует только app/ и foundation_kaia, поэтому canonical core явно staged в app/wakeword_core с проверкой content identity до сборки. Тест образа импортирует runtime без Chara и host source tree.

## Interface

- `readiness() -> TrainingReadiness`: protocol_version=1, installed/resource profile, content hashes, feature-space ID, dependencies/versions, supported input schema, CPU ready, errors. Read-only, без загрузок.
- `describe(training_id: str) -> TrainingStatus`: exists, status, request/execution fingerprints, training_complete, completed stages, error/retryability, result reference if complete. Missing возвращается явно, а network failure не трактуется как missing.
- `train(training_id: str, parameters: TrainingParameters, expected_dataset: DatasetRequirements, dataset: Iterable[bytes] | FileLike) -> Iterable[BrainboxReportItem[TrainingResultReference]]`: websocket streaming, как PiperTraining. Dataset — transport stream/path encoding существующего API, не путь диска клиента.
- `export(result: TrainingResultReference) -> FileLike`: endpoint отдаёт portable result ZIP. Повтор не запускает trainer/inference. Запрашиваемые IDs/fingerprints сверяются; произвольный server path не принимается.

Host создаёт task через WakewordTraining.new_task(id=persisted_task_id).train(..., dataset=local_archive_path). Используется стандартный marshalling; Path передаётся как файл, не JSON-строка сервера. Result DTO маленький; archive скачивается отдельной export-задачей с result_to_file=True/streaming cache. Progress/log format соответствует brainbox_training_pipeline, но submission дополняется persisted identities/reconciliation в новом компоненте.

## Server execution

Небольшой __call__/service method принимает поток, делегирует run controller. Методы: receive_dataset, validate_dataset, bind_background, train_model, select_model, export_model, evaluate_model, render_reports, package_result. Вычисления и IO отдельно; trace/log показывает current stage, actual iterations/updates, validation metrics, переданные bytes и ошибки. Секреты и полные dataset arrays в лог не пишутся.

Training data: четыре NPY portable dataset + собственный ACAV profile. Проверяется expected target set, original positive minimums per split, classes/nonempty/lineage, all hashes/finite float32, feature-space. Никаких hidden repairs/re-synthesis/re-augmentation. Все accepted feature rows используются; training sampler replacement остаётся прежним.

Run directory /resources/training/<training_id> под lock. ID безопасный opaque name, не принимается как относительный путь. Не применять PiperTraining destructive shutil.rmtree при повторе. Existing run:

- request mismatch -> incompatible, новый output/training_id;
- receiving/validating без начала training -> переиспользовать проверенные transfer artifacts, повторить незавершённую проверку;
- interrupted optimizer -> partial_training_requires_new_id, без resume;
- verified training_complete -> завершить следующие стадии без новых updates;
- complete -> прежний result-reference;
- running locked -> running/busy, второй optimizer не запускается.

Server stage hashes проверяются до skip; порча критического trained-state/history не исправляется скрытым обучением. Отсутствие только HTML допускает rebuild из primary artifacts. Portable export не требует PT на хосте, но внутреннее состояние остаётся на сервере для audit/recovery. Автоматического удаления run после export нет.

## Completion and failure

Не менее одного настоящего update, три завершённые стадии, проверенный ONNX, final ORT scores, metrics/history/snapshot и оба HTML обязательны. Низкий recall не делает smoke технически failed. Server completion marker публикуется последним; затем result reference связан с immutable output hashes. Host complete — отдельный marker после скачивания/проверки.

Ошибки передаются принятой в соседних marshalling-сервисах диагностикой stage/reason (exception text). Следующие имена обозначают категории диагностики, а не новый структурированный transport: input_invalid, resource_not_ready, incompatible, running, partial_training_requires_new_id, export_failed, result_missing, transport_unknown. За исключением явно безопасных этапов, новый training attempt не выбирается автоматически после произвольной ошибки.


Actual progress/status payloads use protocol_version=1 and JSON metadata. `describe` reports exists/status/training_complete/error_stage/reference. Diagnostics currently carry stage/reason text; not every proposed error code is a structured field. A separate structured error transport is not introduced; existing BrainBox job errors carry the diagnostic text. Background repair checks hashes even when installation.yaml exists and is available only through explicit install/prepare.

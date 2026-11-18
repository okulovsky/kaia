# Tasks: Генерация корпуса и удалённое обучение wakeword

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/{pipelines,dataset,decider}.md, quickstart.md в этой feature.
**Пути**: от корня kaia. Документы этой feature: chara/wakeword/specs/003-brainbox-wakeword-pipelines/.
**Организация**: US1 — переносимый корпус (P1); US2 — remote обучение (P1); US3 — подготовка/восстановление без Make (P2).
**Tests**: включены по явно требуемым regression/fault/native проверкам SC-001–008. Контрактные тесты писать перед соответствующей реализацией; mock не заменяет native CPU/remote проверку.
**Ограничения**: новый decider разрешён, fundamental framework/общие Chara helpers не менять. Ответы A/C/A: синтетические негативы передаются с позитивами; только признаки+manifest; назад ONNX/два отчёта/primary artifacts без checkpoints. Конституция — неутверждённый шаблон.

## Phase 1: Setup

- [X] T001 Зафиксировать исходные regression команды, версии, текущие метрики/форматы и переносимые fixture в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md; изучить реальные Chara/voice_clone/paraphrasing и существующие wakeword outputs без повторного синтеза.
- [X] T002 Создать lazy package boundaries brainbox/pipelines/__init__.py, chara/wakeword/__init__.py, generation/__init__.py, training/__init__.py, core/__init__.py, scripts/__init__.py под chara/wakeword/; импорт package/config не запускает Chara, ML или соединение с сервером.
- [X] T003 [P] Подготовить chara/wakeword/tests/remote_training_fixtures.py: небольшие numeric NPY, отдельные lineage по четырём частям, legacy/portable manifests, ACAV train/validation и result ZIP fixture; явно тестовое происхождение, без downloads/TTS. После T002, независимо от переноса core.

## Phase 2: Foundational — блокирует истории

- [X] T004 Определить DTO UnifiedConfiguration, PortableDatasetManifest, DatasetRequirements, BackgroundResourceProfile, TrainingRequest/Status/ResultReference, PortableResultManifest и LocalTrainingResult в brainbox/deciders/voice_analysis/wakeword_training/runtime/dto.py: «schema_version=1», «status=complete», «shape=(N,16,96), N>0», четыре обязательные роли, original counts отдельно от rows, server checkpoint references только metadata.
- [X] T005 [P] Перенести settings readers в brainbox/deciders/voice_analysis/wakeword_training/runtime/settings.py: generation/training sections и отдельные `_comments`, минимумы позитивов train/validation, «casefold, whitespace collapse, sorted unique» для variants; ожидания из явной config, не из manifest; JSON paths относительно JSON, comments/host paths вне content fingerprint; сохранить старые numeric constraints и full/smoke defaults.
- [X] T006 [P] Перенести lightweight atomic JSON/hash/output-lock helpers в brainbox/deciders/voice_analysis/wakeword_training/runtime/io.py и state.py: безопасные ID, отдельные background/run/output locks, temporary->verify->publish, metadata content fingerprints; без импортов Chara/torch/ORT/NumPy для host orchestration.
- [X] T007 Реализовать portable manifest/header/hash/lineage validation в brainbox/deciders/voice_analysis/wakeword_training/runtime/manifests.py: четыре float32 части, «Один lineage не пересекает train/validation», source original counts по уникальным IDs, shape/dtype/byte-size/hash, target/minimum counts, feature-space; stdlib finite scan чанками «262144 значениями» с byte order до upload.
- [X] T008 Реализовать bounded ZIP IO в brainbox/deciders/voice_analysis/wakeword_training/runtime/archives.py: input allowlist ровно manifest.json+4 NPY, streaming hashes/CRC, без links/encryption/absolute/UNC/drive/.. /duplicates/case collisions; «2 GiB input expanded/compressed» configurable budget проверяется и в потоке; output отдельный allowlist, распаковка не перезаписывает resources/другой run.
- [X] T009 [P] Добавить chara/wakeword/tests/test_remote_dataset_contract.py: неверный target, недобор original counts при достаточных augmented rows, NaN/Inf, shapes/hashes/dtype, overlapping lineage, unsafe ZIP/zip bomb/byte-order, отсутствие WAV/ACAV/PT в payload; проверить отказ до upload/update.
- [X] T010 Проверить foundational контракт и import isolation в chara/wakeword/tests/test_wakeword_import_boundaries.py: новый package/config/host archive checks без Chara cycle и ML imports; выполнить T009 и записать результаты в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md. Все истории зависят от T001–T010.

## Phase 3: US1 — переносимый корпус (P1, первый increment)

**Цель**: отдельный generate даёт полный корпус и feature-only ZIP, обучение не вызывается.
**Independent test**: малый generation run с четырьмя частями, 3N/review/batches, переносимый ZIP и повтор без TTS.

- [X] T011 [P] [US1] Добавить chara/wakeword/tests/test_generation_portable_pipeline.py: четыре части, no trainer call, сохранение Parler/Vosk crop, confidence/3N/review, actual counts, artifact hashes и repack без изменения NPY bytes.
- [X] T012 [P] [US1] Добавить chara/wakeword/tests/test_legacy_dataset_adapter.py: compatible старый generation manifest/resources.json преобразуется без TTS; test->validation mapping, непереносимые paths не включаются; incompatible source явно отвергается.
- [X] T013 [US1] Перенести текущие generation settings-independent collection/positives/negatives/local/verification/progress/review компоненты из chara/wakeword/generation/ в chara/wakeword/generation/; оставить алгоритмы и Chara stage names, durable task/batch IDs, Parler обоих классов и host аугментации неизменными, без второй реализации.
- [X] T014 [US1] Реализовать chara/wakeword/generation/packaging.py: адаптер legacy manifest, переносимые preparation/feature-space identities, actual original/feature counts, lineage, summary review без raw records; ZIP ровно 5 файлов, без WAV/PT/background/resources.json, данные не пересчитываются.
- [X] T015 [US1] Собрать GenerationPipeline в chara/wakeword/generation_pipeline.py: validate_configuration -> check/prepare resources -> collect -> normalize/review -> extract_features -> validate_corpus -> package_dataset -> publish_result; каждый этап метод, __call__ без архивных/IO циклов; compatible complete проверять до Chara cache.
- [X] T016 [US1] Добавить независимый entry point chara/wakeword/scripts/generate.py и lazy exports generate_dataset/GenerationPipeline; явные config/output/BrainBox URL, return GenerationResult, codes 0/1/2; training decider не требуется для generate.
- [X] T017 [US1] Обновить chara/wakeword/__init__.py и scripts/generate.py как тонкие deprecated generation wrappers, перенаправить существующие generation tests на canonical код без дублирования business logic; сохранить старые пользовательские outputs без перезаписи.
- [ ] T018 [US1] Выполнить T011/T012 и generation regression tests в chara/wakeword/tests/, repack реального совместимого корпуса и один отдельный малый реальный generation run при доступных Parler/Vosk; подтвердить no trainer, batching/3N/review/ZIP и actual bytes в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md.

## Phase 4: US2 — удалённое обучение и локальный результат (P1)

**Цель**: новый WakewordTraining получает признаки через dataset API и возвращает проверенные ONNX/оба отчёта/primary artifacts без общего диска.
**Independent test**: numeric fixture -> настоящий Linux CPU update/export/report -> portable export -> host verify/offline rebuild без PT и сервера. Для сквозной интеграции используется US1; unit/decider проверки допускают contract fixture без US1 runtime.

- [X] T019 [P] [US2] Добавить chara/wakeword/tests/test_training_decider_contract.py: FileLike streaming dataset, readiness/describe/train/export DTO, expected variants/counts, server повтор hash/finite/profile проверок до update, окончательный BrainboxReportItem.result — маленькая ссылка, не bytes архива.
- [X] T020 [P] [US2] Добавить chara/wakeword/tests/test_portable_training_results.py: portable manifest не требует PT/final-state/background/source dataset, реальные score counters и идентичность ONNX; report-only без BrainBox/torch/ORT/inference, два языка/порядок секций и отказ при порче primary files.
- [X] T021 [US2] Перенести model/batches/trainer/checkpoints/metrics/validation/export из chara/wakeword/training/ в brainbox/deciders/voice_analysis/wakeword_training/runtime/ без Chara; сохранить три стадии, hard mining/accumulation/flush, percentile/fallback/averaging, bounded windows L-16+1 и последующую оценку именно ONNX. Адаптировать существующие численные tests к единственному core.
- [X] T022 [US2] Реализовать brainbox/deciders/voice_analysis/wakeword_training/runtime/inputs.py и background.py: portable four NPY + installed resource manifest, NumPy mmap finite scan без pickle; «Background train=(N,T,96); validation flattened=(M,96), M%T=0», отдельные сегменты/stride1/.08 и waveform_hours=null, отсутствие re-augmentation и host path reads.
- [X] T023 [US2] Реализовать server execution lifecycle в brainbox/deciders/voice_analysis/wakeword_training/runtime/execution.py и state.py: receive/validate/bind/training/select/export/evaluate/report, immutable training_id/request/execution fingerprints, validated stage hashes. Отдельно training_complete до selection, interrupted optimizer требует новый ID, поздний сбой не вызывает updates, locks исключают второго писателя.
- [X] T024 [US2] Перенести rendering в brainbox/deciders/voice_analysis/wakeword_training/runtime/reporting.py: English report.html/Russian report_ru.html, метрики -> curves -> data, без raw JSON; verified portable sources, local rebuild из scores/history/config/snapshot без PT/source corpus/background, checksums обоих отчётов обновлять атомарно.
- [X] T025 [US2] Реализовать brainbox/deciders/voice_analysis/wakeword_training/app/result_export.py и core/manifests.py: внутренний completion marker с PT отделён от portable result-manifest; export allowlist из contracts/dataset.md, streaming ZIP/reference hashes/size, checkpoints и input/background не включать, повтор export не тренирует.
- [X] T026 [US2] Создать interface.py/api.py/settings.py в brainbox/deciders/voice_analysis/wakeword_training/ и app/interface.py: readiness(protocol_version=1), describe, websocket train(training_id,parameters,expected_dataset,dataset:FileLike), export(reference)->FileLike по PiperTraining; типы из T004, без новых fundamental transport функций.
- [X] T027 [US2] Создать files/resource-profile.json и app/installer.py в brainbox/deciders/voice_analysis/wakeword_training/: закреплённые ACAV source revision/hash и совместимый feature-space, первые floor(N/10) train и следующие floor(N/100) validation, metadata T/сегментов/derived hashes; explicit install/repair, проверка места/temporary/hash/publish, installation.yaml не заменяет проверку файлов. FMA/MITRIR/Parler/Vosk не скачивать для training.
- [X] T028 [US2] Создать app/service.py, app/training_process.py и app/main.py в brainbox/deciders/voice_analysis/wakeword_training/: receive stream с budget, server checks и core stages, BrainboxReportItem progress/log/result-reference, readiness без downloads, describe missing/running/partial/complete, отказ без destructive reset существующего run.
- [X] T029 [US2] Создать brainbox/deciders/voice_analysis/wakeword_training/controller.py, run.py, __init__.py и runtime/build requirements*: DockerMarshallingController/Installer, Linux Python3.11 CPU image с закреплёнными torch2.2.2+cpu/NumPy1.26.4/ONNX1.16.1/ORT1.17.3/Matplotlib3.9.2; canonical core staged как app/wakeword_core с source identity. Не рассчитывать на автоматическое копирование brainbox/chara builder-ом и не менять framework.
- [X] T030 [US2] Зарегистрировать WakewordTraining в brainbox/deciders/voice_analysis/__init__.py и принятом discovery; добавить self-test в brainbox/deciders/voice_analysis/wakeword_training/controller.py: реальный CPU update -> selection -> ONNX/checker/ORT/parity -> reports -> result ZIP на fixture без TTS/downloads. Проверить runtime imports без Chara/host tree.
- [X] T031 [US2] Реализовать chara/wakeword/training/submission.py: persist training_id/task attempt/batch before submission, стандартный FileLike dataset, reconcile existing/missing/unknown; логировать progress как brainbox_training_pipeline, но без его blind api.add retry. Finished failed late stage допускает новый persisted job attempt для того же server training_id, не повтор DB ID.
- [X] T032 [US2] Реализовать chara/wakeword/training/results.py: отдельная export task и streaming download в temporary, verify reference/portable hashes/allowlist/model-metrics/snapshot/counts до local complete; повтор получения не вызывает train, cached file path не считается доказательством наличия файлов, auto cleanup server run запрещён.
- [X] T033 [US2] Собрать TrainingPipeline в chara/wakeword/training_pipeline.py: validate_source -> prepare_archive -> check_remote -> persist_request -> submit/reconcile -> follow -> export -> download -> verify -> publish; методы по этапам, output lock/fingerprints, local complete до API при повторе, без импортов локального ML/audio stack.
- [X] T034 [US2] Добавить chara/wakeword/scripts/train.py и report.py, lazy train_dataset/render_training_report exports; folder generation принимается отдельно от training output, expected word/минимумы из явной unified config, обе HTML локально восстанавливаются без server checkpoints/BrainBox/inference, codes 0/1/2.
- [X] T035 [US2] Создать chara/wakeword/tests/test_remote_training_pipeline.py: no generation/TTS calls, FileLike bytes вместо server path, сначала rejection invalid corpus, running/unknown statuses, header/finite preflight без NumPy/torch, download failure без нового trainer, local cached complete при offline server.
- [ ] T036 [US2] Выполнить Linux image build/native self-test WakewordTraining из controller.py; проверить separate lock/wheel compatibility и generated core content, CPU batches1/>1, parity, actual updates и экспорта без PT; записать реальные результаты в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md, не объявлять mock self-test native проверкой.
- [ ] T037 [US2] Выполнить remote smoke по chara/wakeword/specs/003-brainbox-wakeword-pipelines/quickstart.md с сервером без host mounts и клиентом без ML-стека; вернуть ONNX/два отчёта/primary artifacts, зафиксировать actual corpus/resource hashes, network bytes, updates и final metrics в validation.md этой feature.
- [X] T038 [US2] Проверить T020/T035 и реальную offline пересборку обоих отчётов после отключения BrainBox и отсутствия локальных PT: unchanged model/history/scores hashes и совпадение чисел; записать proof в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md. Пользовательский MVP — US1+US2, включая доступный вручную install decider-а.

## Phase 5: US3 — подготовка, восстановление и Python интерфейс (P2)

**Цель**: установка/проверки и устойчивые повторы без Make и без скрытого обучения.
**Independent test**: explicit prepare + повтор без downloads; fault scenarios до/после обучения, независимое восстановление download, concurrent/incompatible отказ.

- [X] T039 [P] [US3] Добавить chara/wakeword/tests/test_wakeword_environment.py: generation/training/all scopes, read-only check-only, registered/image/service/profile states, instruction для недоступного/устаревшего сервера, training-only не проверяет local torch/FFmpeg/FMA/Parler/Vosk, idempotent install и повреждённый фон.
- [X] T040 [P] [US3] Добавить chara/wakeword/tests/test_remote_training_lifecycle.py: lost response после commit, offline reconciliation не missing, partial optimizer/new ID, late selection/export/evaluate/report failure no updates, lost download no trainer, fingerprint mismatch/no overwrite и locks; snapshots counters/hashes до/после.
- [X] T041 [US3] Реализовать scoped check/explicit setup в chara/wakeword/environment.py и scripts/prepare.py: --scope generation|training|all, --check-only; стандартные controller install/resource API, серверный source update/restart объясняется пользователю, не делается клиентом; pip замена DLL только после отдельного host preflight процесса генерации.
- [X] T042 [US3] Дополнить brainbox/deciders/voice_analysis/wakeword_training/runtime/state.py и app/service.py обучающего decider-а проверками всех recovery состояний из T040: busy/running, mismatch, interrupted partial, training_complete late retry, corrupted trained artifacts не исправлять скрытым retrain; серверный фон не удаляется при очистке временного dataset.
- [X] T043 [US3] Завершить durable follow/recovery в chara/wakeword/training/submission.py и results.py: describe server status перед новым attempt, сверка request/execution fingerprints и received hash, export повторяется независимо, result_missing диагностируется без нового обучения; выполнить T040.
- [X] T044 [US3] Обновить chara/wakeword/learn-settings.json, settings/smoke.json и остальные settings/ конфигурации: explicit expected target/minimum original positives, server resource profile, единые immutable compatibility IDs; сохранить counts6000/full recipe и counts8/smoke, English `_comments` раздельно, host-relative resource paths не отправлять серверу.
- [X] T045 [US3] Удалить chara/wakeword/Makefile; заменить scripts/manage.py и generation_manage.py тонкими Python compatibility wrappers новых prepare/generate/train/report entry points; старый full run делегирует двум pipeline, не вызывает host trainer. Обновить __init__.py migration exports без циклов и второй реализации.
- [ ] T046 [US3] Выполнить T039/T040 и сценарии prepare/retry/concurrency/partial/late-failure/download из quickstart.md; записать actual counters/hash comparisons, установочные и сетевые ограничения в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md; непроведённые проверки явно оставить непроведёнными.
- [X] T047 [US3] Проверить через chara/wakeword/tests/test_wakeword_import_boundaries.py и test_remote_training_pipeline.py все новые scripts --help/exit codes, explicit custom config, no implicit smoke, offline report и local complete, отсутствие Make в обязательных сценариях и работоспособность thin deprecated imports.

## Phase 6: Polish и сквозная приёмка

- [X] T048 [P] Обновить chara/wakeword/README.md и specs/003-brainbox-wakeword-pipelines/quickstart.md под реализованные Python команды, host/server prerequisites/paths, decider registration/update/restart, features-only ZIP, datasets vs background, report-only deps, full/smoke и weak quality disclaimer; убрать future-only описания только у реализованных команд.
- [X] T049 Выполнить полную регрессию chara/wakeword/tests/ на Windows/Python3.12, native/import/remote-client subset на Python3.11, Ruff и mypy на chara/wakeword/, новом decider и изменённых wrappers/tests; исправить нарушения в соответствующих модулях, записать точные counts/skips/versions в validation.md этой feature.
- [ ] T050 Выполнить полный curriculum на доступном реальном проверенном корпусе через новый remote pipeline по quickstart.md и сохранить actual volumes/updates/time/selected states/final metrics/артефакты в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md; готовый корпус repack, без автоматического нового TTS. Малый корпус явно не объявлять production-quality проверкой.
- [X] T051 Проверить bounded processing/архивные budgets и измерить dataset/result bytes, server/host time/RSS для brainbox/deciders/voice_analysis/wakeword_training/runtime/archives.py, inputs.py, batches.py и export/download; два разных корпуса используют один background profile без повторной загрузки. Сохранить измеренный scope и ограничения в validation.md этой feature, не придумывать SLA.
- [X] T052 Проверить архитектуру в chara/wakeword/generation_pipeline.py, training/pipeline.py и brainbox/deciders/voice_analysis/wakeword_training/app/service.py: __call__/run показывают этапы, IO/validation/cache/transfer/compute/report/errors разнесены по методам, нет дублированного trainer и импортов старого host training из image; сопоставить стиль с voice_clone/paraphrasing и устранить оставшиеся монолиты.
- [X] T053 Сверить contracts/dataset.md, contracts/decider.md и contracts/pipelines.md этой feature с фактическими DTO/CLI/архивами в brainbox/deciders/voice_analysis/wakeword_training/runtime/ и новом decider; обновить дизайн только по обоснованным реализованным отклонениям, сохраняющим ответы A/C/A; не менять согласованный scope молча.
- [ ] T054 Заполнить FR-001–021/SC-001–008 evidence matrix и ограничения в chara/wakeword/specs/003-brainbox-wakeword-pipelines/validation.md; проверить реальный ONNX, два отчёта, primary artifacts, no Make, remote filesystem isolation и no duplicate updates. Отмечать выполненными только подтверждённые задачи, не выдавать отсутствие внешнего сервера за успешную проверку.

## Dependencies & Execution Order

- Setup: T001 -> T002 -> T003. Foundations: T004 -> (T005 ∥ T006) -> T007 -> T008; T009 пишется независимо по стабильному контракту после T004 и завершается до T010; T010 ждёт T003–T009.
- US1: (T011 ∥ T012) -> T013 -> T014 -> T015 -> T016 -> T017 -> T018. Runtime US1 не зависит от нового training decider-а.
- US2: (T019 ∥ T020) -> T021 -> T022 -> T023 -> T024 -> T025 -> T026 -> T027 -> T028 -> T029 -> T030 -> T031 -> T032 -> T033 -> T034 -> T035 -> T036 -> T037 -> T038. Core/decider unit work возможно на contract fixture после foundations; T033/T037 используют результаты US1; native self-test T036 требует image и всех server stages, remote T037 ждёт T018/T036 и T041/T044; реализацию T039/T041/T044 выполнить до T037, затем продолжить US3.
- US3: (T039 ∥ T040) -> T041 -> T042 -> T043 -> T044 -> T045 -> T046 -> T047. Проверяемые recovery primitives уже предусмотрены в US2; US3 завершает scope-aware подготовку, fault coverage и удаление Make.
- Polish: после T047; T048 docs может идти независимо от T049 checks, остальные T050–T054 последовательно, так как меняют общий validation.md. При сбое обязательной последовательной задачи сначала устранить причину; не отмечать проверку завершённой по наличию кода.

## Parallel Opportunities

`[P]` означает независимые файлы после выполненных prerequisites, не разрешение запускать агентов само по себе.

- Foundations: T005 settings и T006 IO/state; T009 contract tests не меняет implementation files.
- US1: T011 generation flow tests и T012 legacy adapter tests.
- US2: T019 decider interface tests и T020 portable report tests. Не параллелить T021–T025, затрагивающие общие core manifests/state, без отдельной координации.
- US3: T039 environment tests и T040 lifecycle tests; T041–T045 выполняются последовательно из-за общих orchestration/state/config.
- Polish: T048 documentation вместе с T049 regression; записи в validation.md согласовывать последовательно.

## Implementation Strategy

1. Зафиксировать действующее поведение и контракты, затем изолировать core от Chara/host imports.
2. Первый increment — US1: полный переносимый корпус и ZIP без обучения.
3. Пользовательский MVP новой архитектуры — US1+US2: реальные remote updates, проверенный ONNX и локальные отчёты/primary artifacts. US1 сам по себе не объявлять завершением всей feature.
4. US3 завершает explicit preparation, надёжный recovery и миграцию от Make. Не переносить destructive reset из PiperTraining или blind api.add retry из общего helper.
5. Финальная приёмка требует native Linux и remote/no-shared-path proof, а не только mocks. При недоступных ресурсах сохранять незакрытые проверки с причиной.

## Requirement Traceability

| Требования | Задачи |
|---|---|
| FR-001, FR-017–018, SC-007 | T002, T013–017, T026–034, T041, T045, T047–049, T052 |
| FR-002–005, SC-001 | T007–018, T044, T049 |
| FR-006–007, SC-004 | T022, T027–030, T039, T041, T051 |
| FR-008–011, SC-003 | T004–010, T019, T022, T028, T031, T033, T035–037 |
| FR-012–014, SC-002 | T021–023, T028–030, T036–038, T050 |
| FR-015–016, SC-005 | T020, T024–025, T032, T034, T038 |
| FR-019–020, SC-006 | T006, T023, T031–033, T035, T040, T042–043, T046–047 |
| FR-021 | T005, T034, T041, T044–045, T048, T053 |
| SC-008 и сквозная приёмка | T018, T036–038, T046, T049–054 |


## Implementation checkpoint — 2026-11-17

48/54 tasks completed in the documented local scope. T018/T036/T037/T046/T050/T054 remain unchecked because actual Linux/Docker/remote/full acceptance is unavailable. See validation.md for exact commands, native artifacts, metrics, source/transport distinctions and the existing Chara/NumPy infrastructure constraint. Some test responsibilities are combined across existing numeric regression files and new contract/lifecycle files rather than duplicated under every planned filename. No checklist markers were modified.

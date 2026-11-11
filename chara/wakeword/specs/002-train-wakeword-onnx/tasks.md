# Tasks: Обучение wakeword, ONNX и достоверный отчёт

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/cli.md, contracts/artifacts.md, quickstart.md в specs/002-train-wakeword-onnx/.
**Уточнения**: 2026-11-09, A — «пороговые окна/ч» по времени признаков, без независимых аудиособытий; B — прерванный optimizer loop не продолжается, новый запуск в новом output на готовых данных.
**Пути**: относительно chara/wakeword, если не указан полный путь. Существующую generation/ не переписывать. Конституция — неутверждённый шаблон, её комментарии не являются требованиями.
**Tests**: включены по проверкам и критериям spec.md. Тесты соответствующей истории пишутся до реализации и должны выявлять отсутствие поведения; численные fixture не выдаются за результаты реального обучения.
**Format**: - [ ] TNNN [P при независимости] [USn в фазах историй] действие с точными путями. [P] не снимает указанных ниже зависимостей и не означает разрешение запускать агентов.

## Phase 1: Setup

**Цель**: подготовить структуру и воспроизводимое окружение без изменения действующей генерации.

- [X] T001 Создать training/__init__.py и каркас пакета training/ по plan.md; зафиксировать lazy-import boundary: settings/report не загружают модель и не обращаются к BrainBox; сохранить существующие generation/ и корневой data-only run без изменения поведения.
- [X] T002 Добавить onnx==1.16.1 и явный renderer Matplotlib 3.9.2 в requirements-host.txt, согласовать requirements-host.lock.txt с torch 2.2.2+cpu, NumPy 1.26.4 и ORT 1.17.3; проверить установку в отдельном окружении Windows/Python 3.12 и записать команды/версии в specs/002-train-wakeword-onnx/validation.md, не переустанавливая библиотеки внутри процесса с загруженными DLL.
- [X] T003 [P] Создать examples/training-smoke.json и examples/training-full.json: smoke stage_steps=[8,4,4], batch_counts=2/2/4, accumulation_examples=8, max_negative_weight=10; full stage_steps=[20000,2000,2000], batch_counts=32/32/64, accumulation_examples=128, max_negative_weight=1500; LR=[1e-4,1e-5,1e-6], threshold=0.5, target_window_fp_per_hour=0.5, device=cpu; не вводить скрытые минимумы стадий в smoke. Зависит только от T001, может выполняться вместе с T002.

## Phase 2: Foundational — блокирующие основания

**Цель**: контракты данных/конфигурации и безопасный доступ к входам до любого обновления модели.

- [X] T004 [P] Добавить tests/test_training_inputs.py для неверных settings, отсутствующих/пустых/NaN/нечисловых массивов, несоответствия хешей/форм/классов и ACAV provenance; включить fixture helper tests/training_fixtures.py с четырьмя реальными числовыми NPY и небольшими ACAV train/val, явным manifest и сегментацией, без загрузок и синтеза.
- [X] T005 [P] Определить TrainingSettings-related DTO, DatasetSnapshot, HistoryEvent, CheckpointSelection, ExportCheck, ValidationResult, TrainingResult и FullRunResult в training/dto.py по data-model.md: идентичности/хеши, stage status, actual counts, scores paths/order; nullable поля сохраняют причину недоступности; «waveform_hours optional/null» не подменяется временем признаков, final metrics связаны с model_sha256.
- [X] T006 Реализовать training/settings.py и чтение двух examples/training-*.json: «schema_version=1», «device=cpu/auto/cuda», «mode=smoke/production», stage_steps[3]/stage_learning_rates[3]/validation_start_fractions[3]; «Все counts/steps/batch/threads — положительные целые без bool», «LR и веса конечны и положительны; threshold в [0,1]; seed в поддерживаемом диапазоне; три стадии обязательны»; fractions конечны в [0,1], начало 1 означает только завершающую оценку. Model_name — безопасное имя либо из manifest, JSON paths относительно JSON. Сохранить canonical requested/resolved device и export tolerances, reject недоступную явно запрошенную cuda.
- [X] T007 Реализовать supervised resolver и DatasetSnapshot в training/inputs.py: generation root или dataset/ через manifest; «actual_shape=(N,16,96)», N>0, numeric/finite чанками, mmap с allow_pickle=False, фактические counts из файлов отдельно от исходных WAV counts и lineage; проверить все хеши/разделение, сохранить settings/sources/review и unavailable durations/speakers с причиной; bare NPY без manifest отвергать.
- [X] T008 Дополнить training/inputs.py ACAV adapter: «Background train: file/hash/shape=(N,T,96), N>0,T≥16»; validation=(M,96), T из согласованной ACAV train того же resource item, M делится на T; для --background-manifest требовать явные segment lengths/source hashes/frame_step_seconds. Сохранить sum(max(0,L-16+1)), оценённые кадры и исключения; исключить cross-row/cross-split окна, отвергать нулевой exposure и неизвестную обязательную временную базу, не скачивать ресурсы.
- [X] T009 Реализовать в training/state.py общие atomic metadata/history/checkpoint writers, run_id, output lock и структуры stage_status/error_stage, используя лёгкие IO/hash/lock helpers generation/io.py и generation/run_state.py; до update формировать config/data/backend/version fingerprint. Не принимать один лишь размер/mtime за доказательство совместимости; полный cache/retry lifecycle завершает US3.
- [X] T010 Реализовать training/dependencies.py: scoped проверка torch/NumPy/ONNX/ORT/Matplotlib и resolved device, без BrainBox/Parler/Vosk/FFmpeg/audio-preparation checks; проблемы возвращать как preflight diagnostics. Report-only требует только renderer/числовое чтение и не загружает torch/ONNX-модель; Make-интеграция выполняется в US3.

**Checkpoint**: settings/DTO/input/state контракты стабильны, T004 проходит, snapshot проверяется до model update. Все истории зависят от T001–T010.

## Phase 3: US1 — Обученная ONNX-модель из готового датасета (P1)

**Цель**: настоящее обучение → selection → проверенный ONNX → измеренные final scores/metrics, без новой генерации.
**Independent Test**: один CPU fixture run с ≥1 optimizer update, исходными данными только из snapshot и batches 1/>1 в ORT. До US2 результат стадии model_ready не считается завершением всей feature и не публикует full complete без HTML.

### Tests US1 — сначала

- [X] T011 [P] [US1] Добавить tests/test_training_loop.py для seed/sampling, L=16 → одного окна, окон без пересечения сегментов, bounded mmap batches, трёх стадий, LR/negative-weight adaptation, hard mining, accumulation, flush remainder до финальной оценки, zero-update refusal и раздельных iteration/update counters; assert loss только после настоящего optimizer.step.
- [X] T012 [P] [US1] Добавить tests/test_training_metrics.py с точными fixture TP/FP/TN/FN, precision без положительных предсказаний, F1 напрямую, boundary score==threshold, окна/ч с frame_step=0.08 и нулевым exposure; метрика не называется независимыми аудиособытиями, отсутствующая waveform duration остаётся null.
- [X] T013 [P] [US1] Добавить tests/test_training_selection.py для candidate gate с третьей валидации, p50/p5 с текущим событием, пересечения p90/p90/p10, tie-break по раннему event, пустого отбора/пустого списка, tensor averaging и различия финальных метрик от средних checkpoint metrics.
- [X] T014 [P] [US1] Добавить tests/test_training_export.py с настоящими checker/ORT, sigmoid и float32 input [B,16,96] → output [B,1], batches 1/>1, finite/range, parity по atol=1e-5/rtol=1e-4, намеренно повреждённым ONNX и failure без публикации успешного артефакта.
- [X] T015 [P] [US1] Добавить tests/test_training_pipeline.py: реальное малое CPU обучение, selection/export/final evaluation и фактические массивы scores; запретить вызовы generation.run, BrainBox, скрытые downloads и fake-success при zero updates; snapshot и final model hash должны соответствовать измерениям, фаза до HTML — только model_ready.

### Implementation US1

- [X] T016 [P] [US1] Реализовать training/model.py по cell 28: Flatten → Linear(1536,128) → LayerNorm(128) → ReLU → Linear(128,1), training output logits; отдельная export wrapper включает sigmoid, model state не меняется при измерении. Независимо от T017/T018 после оснований и тестов.
- [X] T017 [P] [US1] Реализовать training/batches.py: sampling с возвращением в supervised mmap и random ACAV row/start, приведение только партии к float32; validation итератор сегментов со stride 1 и числом L-16+1, компактный score-index mapping; не материализовать весь корпус или sliding-window array. Независимо от T016/T018.
- [X] T018 [P] [US1] Реализовать training/metrics.py с формулами contracts/artifacts.md: «Precision: null при TP+FP=0», F1=2TP/(2TP+FP+FN), score≥threshold, отдельный фон; feature_equivalent_hours=evaluated_frames×0.08/3600, zero exposure failure; запрет NaN/Infinity в опубликованных JSON, undefined → null+reason. Независимо от T016/T017.
- [X] T019 [US1] Реализовать atomic candidate persistence и selection в training/checkpoints.py: с третьего validation n_fp≤p50 и recall≥p5, финальное p90 accuracy/p90 recall/p10 window rate, deterministic fallback по FP/hour→recall→earliest event, затем latest trained state при отсутствии кандидатов; сохранить IDs/percentiles/hashes/reason. Усреднять floating tensors текущей модели, новый integer buffer отвергать без новой политики; не подменять final metrics средними кандидатами.
- [X] T020 [US1] Реализовать training/trainer.py на T016–T019: новый Adam для каждой стадии, warmup/hold/cosine notebook, negative ramp и удвоение по минимуму фоновой метрики всей истории, hard filtering >=0.001 negatives / <0.999 positives и accumulation до заданного числа; flush непустого остатка, реальный loss/update/stage/LR/weights/timing в history.jsonl и кандидаты из фактической валидации. Сохранить последнее обученное состояние и index до training_complete; финальные state/selection — отдельный последующий этап.
- [X] T021 [US1] Реализовать training/export.py: legacy torch.onnx.export opset14 без неподдерживаемого dynamo аргумента, input onnx::Flatten_0/output output, dynamic batch; временный файл → checker → CPU ORT → parity на сохранённой deterministic validation sample до 256 background окон и supervised входах → atomic publish. Сохранить ExportCheck, абсолютную ошибку и индексы/допуски; не выпускать успешный результат при несогласованности.
- [X] T022 [US1] Реализовать training/validation.py: после selection/export заново оценить именно итоговый ONNX на всех supervised validation rows и всех допустимых background windows партиями; «Итоговые scores конечны и в [0,1]», число строк совпадает со snapshot. Записать ordered NPY scores (background mmap), metrics.json, model/snapshot hashes, thresholds/counts/exposure/stride и честные unavailable reasons; не брать final rate из history.
- [X] T023 [US1] Собрать training/pipeline.py через Chara stages preflight → training → selecting → exporting → evaluating, с snapshot до update и отдельными verified stage outputs; завершённое обучение не зависит от успешности selection. Предоставить внутренний результат model_ready без фиктивного complete до US2; запретить TTS/BrainBox calls и silent input repair. Выполнить T015 на настоящих update/export.
- [X] T024 [US1] Выполнить независимый native CPU сценарий US1 и записать команды, actual iterations/updates, checkpoint selection, ONNX contract/parity и raw metrics в specs/002-train-wakeword-onnx/validation.md; сравнить итоговые измерения с ONNX scores, не заявлять качество production по fixture и не отмечать US1 проверенной только на mock exporter.

## Phase 4: US2 — Достоверный отчёт (P1)

**Цель**: report.html с порядком validation → curves → data, только из сохранённых первичных измерений.
**Independent Test**: отрендерить сохранённый valid artifact fixture без trainer/inference и проверить все числа, порядок и отсутствие внешних ресурсов. Затем повторить на реальном результате US1.

### Tests US2 — сначала

- [X] T025 [P] [US2] Добавить tests/test_training_reporting.py для трёх первых секций в обязательном порядке, встроенных SVG без CDN, маркера при одной точке, отсутствия дорисованных измерений, раздельных единиц осей, HTML escaping и unknown duration/speaker count с причиной вместо 0; fixture явно тестовый, не реальное обучение.
- [X] T026 [P] [US2] Добавить tests/test_training_report_consistency.py: пересчёт всех агрегатов из saved scores, связь model SHA/snapshot/history, отказ при подмене модели/первичных результатов и отсутствие вызовов train/export/inference при report-only; случай averaging, где history last/best не равен метрикам итоговой модели.

### Implementation US2

- [X] T027 [US2] Реализовать training/reporting.py: загрузка и проверка saved sources, пересчёт metrics через training/metrics.py без inference, Matplotlib Agg/SVG embedded HTML; сначала final metrics (с оконным proxy/методикой), затем реальные loss/update и validation curves по стадиям, затем actual data/source/split/hash/settings/review. «report.html с version/title/run_id/model SHA»; недоступные поля — причина, текст экранирован, smoothing не требуется.
- [X] T028 [US2] Дополнить training/pipeline.py этапом reporting и completion validation всех model/export-check/scores/metrics/history/snapshot/HTML, публиковать manifest.json последним с хешами. Открыть run_training/TrainingSettings через lazy __init__.py и training/__init__.py; добавить scripts/train.py с required dataset/config/output и --background-manifest. Exit0/complete только после обязательного отчёта, без требования BrainBox.
- [X] T029 [US2] Реализовать scripts/report.py и render_training_report в training/reporting.py: rebuild HTML из сохранённых проверенных артефактов, без обучения и получения новых измерений; CLI output именно TRAINING_OUTPUT, коды 0/1/2 по контракту. Не менять модель, scores, history или входной датасет; согласование completed marker при повреждении/пропаже HTML завершает US3.
- [X] T030 [US2] Выполнить T025–T026 и реальную связку train→ONNX→report из quickstart.md, сохранить в specs/002-train-wakeword-onnx/validation.md реальное совпадение чисел с scores, порядок разделов, self-contained открытие и rebuild без update/inference. Только после этого считать готовым пользовательский MVP US1+US2.

## Phase 5: US3 — Повтор, восстановление и полный цикл (P2)

**Цель**: никакого скрытого переобучения/пересинтеза, корректные статусы и понятное восстановление согласно ответу B.
**Independent Test**: compatible complete повтор без update; удалённый HTML восстановлен; несовместимые входы отклонены; interrupted optimizer требует новый output, completed training переживает сбой selection/export/report без новых update.

### Tests US3 — сначала

- [X] T031 [P] [US3] Добавить tests/test_training_lifecycle.py: concurrent output lock, fingerprint mismatch до cache, interrupted training и новый output на прежнем dataset, отказ без смешивания history, fault injection selection/export/evaluation/report после training_complete с неизменным update count; completed артефакты проверяются по хешам, а не одному status.
- [X] T032 [P] [US3] Добавить tests/test_full_pipeline.py: external DATASET не вызывает генерацию/BrainBox и не копируется; новая генерация вызывается только при отсутствии DATASET, full status не равен generation complete, корневой cached complete проверяется до generation preflight; Make/CLI scopes/exit codes и сохранность старого Python generation.run.

### Implementation US3

- [X] T033 [US3] Завершить lifecycle в training/state.py и training/pipeline.py: canonical fingerprint до cache; собственные статусы из data-model.md; interrupted optimizer loop сохраняется и требует новый output, но training_complete определяется сохранённым last-trained state/history/index до selection. Повтор проверенных стадий после selection/export/evaluation/report failure не делает optimizer updates; несовместимость требует новый output без перезаписи, диагностируется error_stage/reason.
- [X] T034 [US3] Реализовать recovery completed отчёта в training/reporting.py, training/state.py и scripts/report.py: если отсутствует только HTML, восстановить его из verified sources и атомарно обновить hash/marker; corrupted ONNX/scores/history не исправлять скрытым training/inference. Повторный полный training run может восстановить только HTML и остаётся связан с той же моделью.
- [X] T035 [US3] Реализовать training/full_pipeline.py и lazy run_full export в __init__.py: новый FULL_OUTPUT/generation при генерации, FULL_OUTPUT/training для обучения, full-run.json связывает statuses/paths/hashes; при DATASET external использовать его snapshot, а не посторонний CONFIG. Старый generation output не преобразовывать неявно в full root; проверить compatible full cache до генерации.
- [X] T036 [US3] Расширить scripts/manage.py и scope-aware checks/setup с training/dependencies.py и generation/environment.py: generation/training/full, training-only без BrainBox/FFmpeg/background WAV checks, full с готовым DATASET использует training preflight; новые зависимости ставятся отдельным preflight/pip процессом Windows. Train/run не скачивают пропавшие inputs, setup не меняет исходный код framework BrainBox или decider.
- [X] T037 [US3] Обновить Makefile и scripts/manage.py для TRAIN_CONFIG/DATASET/SCOPE и целей generate/train/report; make run — full cycle, make generate — прежний data-only; default training-smoke, production только при явном training-full.json. Экранировать пути с пробелами, required DATASET для train, OUTPUT report — каталог обучения, exit0 только при завершении запрошенной операции.
- [X] T038 [US3] Выполнить T031–T032 и сценарии повтора/прерывания/повреждений из quickstart.md, зафиксировать реальные счётчики update/TTS и model/history hashes до/после в specs/002-train-wakeword-onnx/validation.md; доказать отдельно новый запуск после partial training и отсутствие обучения после сбоя следующих стадий.

## Phase 6: Polish и сквозная приёмка

- [X] T039 [P] Обновить README.md и specs/002-train-wakeword-onnx/quickstart.md под фактически реализованные команды, отдельное окружение, новые output paths и статусы; убрать предупреждение «ещё не реализовано», объяснить разницу Vosk confidence и classifier threshold, оконной метрики и реальных событий, smoke и production. Не объявлять model ready по одному generation complete.
- [X] T040 Выполнить полную регрессию tests/ в проверенном окружении Windows/Python 3.12, включая старые generation tests и все native training/export/report tests; исправить выявленные регрессии в соответствующих training/, scripts/ и generation/ файлах, записать точное число тестов/пропусков/версии в specs/002-train-wakeword-onnx/validation.md. Не повторять обучение при одной лишь генерации отчёта.
- [X] T041 Проверить pinned requirements-host.lock.txt и native CPU training/export/report на Python 3.11 в отдельном окружении; записать результат и платформенные ограничения в specs/002-train-wakeword-onnx/validation.md, не считать один успешный запуск Python 3.12 подтверждением обеих версий.
- [X] T042 Выполнить examples/training-full.json на доступном проверенном настоящем generation dataset без автоматического нового синтеза; записать в specs/002-train-wakeword-onnx/validation.md реальный объём данных, 3 стадии/число update, selection, время, final metrics и ONNX/report paths. Если доступен лишь малый датасет, явно назвать это полным curriculum на малом наборе, а не production-quality проверкой; невыполненный полный запуск не объявлять успешным.
- [X] T043 Проверить bounded processing training/inputs.py, training/batches.py и training/validation.py на mmap fixture и реальном доступном ACAV: отсутствие полной contiguous копии окон и всего корпуса на device, число оценённых окон и пропуски; измерить peak memory/time с указанным scope и записать их в specs/002-train-wakeword-onnx/validation.md, не придумывая SLA по одному маленькому примеру.
- [X] T044 Сверить итог с FR-001–FR-021 и SC-001–SC-007, уточнениями A/B и contracts/; заполнить таблицу доказательств и оставшихся ограничений в specs/002-train-wakeword-onnx/validation.md, актуализировать research.md только по фактическим отклонениям. Убедиться, что завершённый пользовательский результат содержит проверенный ONNX и достоверный HTML, а не только признаки или mock-метрики.

## Dependencies & Execution Order

Фазы: Setup T001–T003 → Foundational T004–T010 → US1 T011–T024 → US2 T025–T030 → US3 T031–T038 → Polish T039–T044.

Точная основная цепочка: T001 → (T002 ∥ T003) → (T004 ∥ T005) → T006 → T007 → T008 → T009 → T010 → tests T011–T015 → (T016 ∥ T017 ∥ T018) → T019 → T020 → T021 → T022 → T023 → T024 → tests T025–T026 → T027 → T028 → T029 → T030 → tests T031–T032 → T033 → T034 → T035 → T036 → T037 → T038 → T039–T044.

US1 зависит только от оснований. Renderer US2 независимо тестируется на сохранённом artifact fixture, но его реальная интеграция T028/T030 зависит от US1. US3 зависит от обоих P1 результатов; нет обещания, что полное восстановление можно закончить раньше первичных артефактов. Тесты будущего поведения сначала должны выявлять его отсутствие; native команды выполняются после реализации соответствующих контрактов, не подменяются импортным smoke.

## Parallel Opportunities

- Setup: после T001, T002 requirements/lock и T003 JSON-конфигурации работают с разными файлами.
- Foundations: T004 tests/fixtures и T005 DTO независимы по заданному контракту; T006 уже требует готовые DTO.
- US1: T011–T015 пишутся независимо; после оснований/контрактных тестов T016 model.py, T017 batches.py и T018 metrics.py независимы. Trainer начинается только после них и checkpoint helpers T019.
- US2: T025 reporting tests и T026 consistency tests — разные файлы; T027 renderer строится после тестов. Реальный T030 использует результаты US1, а не mock training.
- US3: T031 lifecycle и T032 full-flow tests независимы; T033–T037 меняют общие orchestration/CLI файлы и выполняются последовательно.
- Polish: T039 README/quickstart может идти одновременно с T040 тестами; задачи, обновляющие общий validation.md, выполняются последовательно или согласованными отдельными секциями.

## Implementation Strategy

1. Основания определяют точные schemas/constraints до модельного кода.
2. US1 даёт технически проверенную обученную модель и primary measurements; это самостоятельный проверяемый прирост, но ещё не полный пользовательский результат.
3. Минимальная поставка по запросу пользователя — US1 + US2: настоящий ONNX, фактические метрики и отчёт с нужным порядком. До HTML не публиковать full complete.
4. US3 завершает контракт команд и надёжное переиспользование; ответ B не заменять автоматическим optimizer resume.
5. Финальная приёмка подтверждает реальные команды и измерения. Отсутствие ресурсов или невыполненные проверки явно отражаются в validation.md и не превращаются в отмеченный успех.

## Requirement Traceability

| Требования / результат | Основные задачи |
|---|---|
| FR-001–FR-004, SC-001 | T003, T006, T015–T024, T028, T035–T037 |
| FR-005–FR-006 | T004, T007–T008, T017, T043 |
| FR-007–FR-008 | T011, T013, T019–T020 |
| FR-009–FR-010, SC-005 | T014, T021, T024, T040–T041 |
| FR-011–FR-012, уточнение A | T012, T018, T022, T026–T027 |
| FR-013–FR-017, SC-003–SC-004 | T025–T030, T034, T039 |
| FR-018–FR-020, уточнение B, SC-002/SC-006 | T009, T023, T028, T031–T038 |
| FR-021 | T002, T010, T036–T037, T039–T040 |
| SC-007 и конечная приёмка | T024, T030, T038, T040–T044 |


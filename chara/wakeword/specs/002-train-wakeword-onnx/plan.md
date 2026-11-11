# Implementation Plan: Обучение wakeword, экспорт ONNX и отчёт

**Branch**: `openWakeWord-eval-perfomance` (фактическая Git-ветка не менялась) | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Feature marker**: `002-train-wakeword-onnx` — значение setup_plan, не новая созданная Git-ветка.

**Input**: `specs/002-train-wakeword-onnx/spec.md`

## Summary

Дополнить текущий пайплайн отдельным host-side обучением и полным циклом до ONNX. Готовые supervised признаки и ACAV переиспользуются; генерация Parler/Vosk и её бюджет/review не меняются. Перенести notebook cells 28/30 с явными исправлениями работы с памятью, окнами и метриками. После отбора/усреднения экспортировать модель с sigmoid, проверить ONNX и заново измерить её показатели. Самодостаточный report.html: сначала метрики итоговой валидации, затем реальные кривые обучения, затем фактически использованные данные.

## Technical Context

**Language/Version**: Python 3.11–3.12; основной проверочный host — Windows/Python 3.12, совместимость 3.11 отдельным smoke.

**Primary Dependencies**: существующие Chara, torch 2.2.2+cpu, NumPy 1.26.4, onnxruntime 1.17.3, Matplotlib 3.9.2; добавить onnx 1.16.1 в direct requirements и host lock. GPU необязателен; запрос cuda при недоступности завершается ошибкой preflight. Framework BrainBox и decider не изменяются.

**Storage**: NPY mmap для признаков и scores, JSON/JSONL для config/snapshots/history/metrics/manifests, PT checkpoints, ONNX и встроенный HTML/SVG. Контроль SHA-256, временные файлы и атомарная публикация, OS-managed output lock.

**Testing**: unittest; численные unit tests, fixture training с реальными update, parity/ORT и report integration, регрессия существующих generation tests. Измерение времени и peak memory на фактическом Windows smoke, без обещания качества production.

**Target Platform**: Windows host с существующим окружением kaia. Генерации нужен доступный BrainBox; training-only и report-only не требуют работающего сервера.

**Project Type**: Python library + CLI + Makefile, без нового web-сервиса.

**Performance Goals**: рабочая память данных ограничивается batch/chunk, не полным ACAV или всеми sliding windows. Smoke с 16 sampling iterations завершается на CPU без скрытых тысяч шагов; полное время фиксируется при реализации, произвольный SLA не обещается.

**Constraints**: итоговый вход (B,16,96), выход (B,1) probability; smoke должен сделать реальный optimizer update. Никаких фиктивных метрик, автоматических загрузок в training/run, перезаписи несовместимых запусков, пересинтеза готового датасета или необъявленного resume. Ошибки обязательных этапов исключают full complete.

**Scale/Scope**: четыре supervised массива текущей feature 001, ACAV train=(N,T,96), ACAV validation=(M,96) с проверенными границами исходных строк; defaults production 20000/2000/2000 sampling steps, три стадии, 20 validation events/stage максимум. Standalone import требует верифицируемые manifest и background provenance.

## Constitution Check

*GATE перед Phase 0*: `.specify/memory/constitution.md` — незаполненный шаблон. Утверждённых принципов нет; текст комментариев не создаёт дополнительных требований. Блокирующих нарушений нет.

Проверены действующие решения пользователя: обучение на хосте; Parler для обоих классов; Vosk для исходной генерации; без Piper/WakewordData и изменений framework. Эта feature явно отменяет старое исключение обучения из feature 001, но не меняет её генерацию.

*GATE после Phase 1*: PASS. Отдельный training package, раздельные fingerprints/status, проверяемый ONNX и сохранённые первичные результаты соответствуют FR-001–FR-021. Решения Phase 0 завершены; открытых NEEDS CLARIFICATION нет. Экспериментальные проверки относятся к реализации, а не скрываются как уже пройденные.

## Project Structure

### Documentation (this feature)

```text
specs/002-train-wakeword-onnx/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   ├── cli.md
│   └── artifacts.md
├── quickstart.md
└── checklists/requirements.md
```

tasks.md создаётся следующим этапом speckit-tasks, не этим планом.

### Source Code (repository root = chara/wakeword)

```text
__init__.py                  # существующий generation API + lazy training/full exports
Makefile                     # check/setup/run; generate/train/report
requirements-host.txt
requirements-host.lock.txt
examples/
  training-smoke.json
  training-full.json
scripts/
  manage.py                  # scope-aware check/setup и full run
  generate.py                # прежний data-only вход
  train.py                   # обучение на готовом датасете
  report.py                  # восстановление отчёта
training/
  __init__.py
  settings.py
  dependencies.py            # training/export preflight без audio/BrainBox checks
  dto.py
  inputs.py                  # проверка manifest, mmap, ACAV provenance
  model.py                   # модель source cell 28
  batches.py                 # bounded sampling/window iteration
  trainer.py                 # стадии, hard mining, update/history, validation
  checkpoints.py             # кандидаты, отбор, averaging/fallback
  metrics.py                 # определения и пересчёт из scores
  validation.py              # bounded итоговое измерение ONNX
  export.py                  # sigmoid, checker, ORT, parity
  state.py                   # fingerprints, lock, stage status и артефакты
  reporting.py               # отчёт из первичных результатов
  pipeline.py                # Chara stages и run_training
  full_pipeline.py           # generation → training, run_full
tests/
  test_training_inputs.py
  test_training_loop.py
  test_training_metrics.py
  test_training_selection.py
  test_training_export.py
  test_training_reporting.py
  test_training_pipeline.py
  test_full_pipeline.py
  (существующие generation tests)
```

**Structure Decision**: реализация обучения в training/, генерация остаётся в generation/, CLI остаётся тонким. Все тесты размещать в общем tests/. Повторно использовать атомарный JSON, хеширование и output lock из generation там, где это не импортирует тяжёлые модели/BrainBox-вызовы. Операции обучения не импортируют удалённый WakewordData и не требуют его кода.

## Phase 0 — Research decisions

Полное обоснование — [research.md](research.md). Ключевые принятые решения:

1. Точный classifier и curriculum notebook; production и короткий smoke используют один trainer.
2. mmap/chunks вместо копии всего корпуса на устройство; окна не пересекают границы ACAV rows, число окон L-16+1.
3. Показатель фона — threshold windows per feature-equivalent hour, с raw count/exposure/stride; не выдаётся за независимые события на аудио.
4. Финальные показатели измеряются заново после selection/averaging и вычисляются по итоговому ONNX.
5. ONNX opset 14 через имеющийся exporter torch 2.2.2 без неподдерживаемого dynamo аргумента; checker + реальное исполнение + parity.
6. HTML восстанавливается из сохранённых scores/history/snapshot без inference или training.

## Phase 1 — Design and contracts

Сущности и состояния: [data-model.md](data-model.md). Команды и границы кэша: [contracts/cli.md](contracts/cli.md). Файлы, формулы и ONNX: [contracts/artifacts.md](contracts/artifacts.md). Сценарии проверки: [quickstart.md](quickstart.md).

Порядок выполнения будущей реализации:

1. Конфигурации и preflight: validate ready dataset manifest/hashes, ACAV boundaries/hashes/time basis, виды данных, backend/device/dependencies; сохранить snapshot до update.
2. Bounded trainer: модель, sampling и schedules, hard mining и accumulation, атомарные checkpoints, журнал реальных update/validation events.
3. Selection/averaging с явным fallback и сохранением final-state.pt; не путать sampling iteration и optimizer update.
4. Экспорт во временный ONNX, structural/run/parity checks; затем итоговое измерение всех validation примеров через ORT и сохранение scores/metrics.
5. Создание отчёта в заданном порядке; проверка пересчёта чисел и self-contained оформления; completion marker последним.
6. Make/CLI/API и full-run orchestration; preserve generation-only API и old output; новые зависимости устанавливать в отдельной preflight/pip фазе, без замены загруженных DLL на Windows.
7. Проверки из quickstart и регрессия генерации. Тесты с фиктивными данными явно отделяются от фактического рабочего обучения; план сам по себе не заявляет успешную реализацию.

## Validation gates and requirement coverage

| Группа | Проверка реализации |
|---|---|
| FR-001–FR-006 | Готовые признаки без синтеза, неверные/пустые/NaN наборы, mmap и запрет cross-split/boundary contamination |
| FR-007–FR-008 | Минимум один update; шаги/стадии/flush/skip; детерминированный отбор кандидатов и fallback |
| FR-009–FR-012 | Реальный export/checker/ORT, batch 1 и >1, parity, пересчёт confusion counts и оконного FP/hour |
| FR-013–FR-017 | Три секции в порядке, графики только из history, NaN/undefined handling, data snapshot, offline report-only |
| FR-018–FR-021 | Никакого full complete без обязательных артефактов; повтор без update, несовместимость fingerprints, сбой экспорта/отчёта, сохранность данных |
| SC-001–SC-007 | Настоящий CPU smoke + проверка артефактов/чисел; отдельный полный рабочий прогон и фиксация времени/объёмов без обещаний production качества |

Нехватка места, отсутствие доступного вычислительного устройства или готового корпуса фиксируются в validation evidence, а не превращаются в фиктивный успешный прогон.

## Complexity Tracking

Нарушений применимых правил нет. Новый пакет training нужен для самостоятельных стадий и cache boundary; новый decider, framework, база данных или сервис не добавляются.


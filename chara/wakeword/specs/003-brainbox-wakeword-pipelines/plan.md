> Уточнение архитектуры 2026-11-18: оркестрация — chara/wakeword/generation_pipeline.py и training_pipeline.py; обучение внутри контейнера — brainbox/deciders/voice_analysis/wakeword_training/runtime. Исторические пути ниже заменены этим разделением.

﻿# Implementation Plan: Два wakeword-пайплайна и удалённое обучение

**Branch**: `openWakeWord-eval-perfomance` — фактическая Git-ветка, не переключалась. Feature marker setup_plan: `003-brainbox-wakeword-pipelines`.
**Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)
**Input**: specs/003-brainbox-wakeword-pipelines/spec.md

## Summary

Перенести orchestration генерации и обучения в chara/wakeword. Генерация через Parler/Vosk остаётся на хосте и дополнительно выпускает portable ZIP только с четырьмя NPY и manifest. Обучающий WakewordTraining decider получает ZIP параметром dataset, использует установленный ACAV фон из собственных ресурсов, обучает прежнюю модель, экспортирует ONNX и создаёт report.html/report_ru.html. Отдельный export/download возвращает модель и первичные результаты без checkpoints. Makefile заменяется Python entry points с читаемыми Chara-этапами.

## Technical Context

**Language/Version**: host Python 3.11–3.12 Windows/Linux; container Linux/Python 3.11 CPU baseline.
**Primary Dependencies**: существующие Chara/BrainBox, DockerMarshallingController, Installer, FileLikeHandler, BrainboxReportItem. ML core: torch 2.2.2+cpu, NumPy 1.26.4, ONNX 1.16.1, ORT 1.17.3, Matplotlib 3.9.2; отдельный Linux lock. Генерация сохраняет прежний host audio stack.
**Storage**: NPY mmap, versioned JSON/JSONL, ZIP; /resources/background и /resources/training/<training_id> на сервере, независимые generation/training output на хосте.
**Testing**: unittest численные/контрактные/regression, Ruff/mypy, native Linux CPU image, настоящий remote filesystem isolation, fault injection submission/download/training.
**Target Platform**: BrainBox на отдельной Linux Docker машине или локальном Docker; локальная ML-среда не нужна для training-only.
**Project Type**: Python library + Chara pipelines + новый training decider; без нового framework или обязательного Make.
**Performance Goals**: bounded mmap/chunk IO, потоковая передача ZIP, никаких WAV/ACAV/checkpoints в обязательном network payload; фиксировать actual bytes/time/RSS, без неподтверждённого SLA.
**Constraints**: сохранение генерации, 3N/review/batch identities, математического рецепта, ONNX [B,16,96] → [B,1], реальных метрик и двух отчётов. Нет общего диска, скрытых downloads при train, automatic optimizer resume или изменения fundamental BrainBox helpers.
**Scale/Scope**: full — 2000 позитивов и 2000 синтетических негативов train, по 1000 validation; 20000/2000/2000 iterations, batch 32/32/64. Smoke — 2 записи/часть и 8/4/4 iterations. Фактическое число feature rows проверяется отдельно от WAV counts.

## Constitution Check

Перед Phase 0: PASS. .specify/memory/constitution.md остаётся незаполненным шаблоном, утверждённых MUST-принципов нет. Ограничения пользователя и уточнения A/C/A обязательны.
После Phase 1: PASS. Нет необоснованных нарушений: отдельный decider прямо запрошен; Chara стиль взят из voice_clone/paraphrasing; reusable core исключает host ML из remote orchestration; framework и соседние helpers не меняются. Опасные участки импорта/передачи/retry имеют отдельные контракты и gate проверки.

## Project Structure

Пути относительно корня kaia; документы feature остаются в chara/wakeword/specs/003-brainbox-wakeword-pipelines.

```text
chara/wakeword/
  __init__.py
  generation_pipeline.py      # canonical generation orchestration
  training_pipeline.py        # canonical remote-training orchestration
  generation/                 # collection, verification, packaging, audio processing
  training/                   # submission, results, compatibility imports within Chara
  environment.py
  scripts/prepare.py, generate.py, train.py, report.py
  requirements-host.txt, requirements-host.lock.txt
  learn-settings.json, settings/
  tests/
brainbox/deciders/voice_analysis/wakeword_training/
  controller.py, api.py, settings.py, run.py, __init__.py
  requirements.txt, requirements.lock.txt
  runtime/                    # canonical training implementation and shared contracts
    settings.py, dto.py, io.py, archives.py, manifests.py
    inputs.py, model.py, batches.py, trainer.py, checkpoints.py
    metrics.py, validation.py, export.py, state.py, reporting.py, execution.py
  app/main.py, interface.py, installer.py, service.py, training_process.py
  files/resource-profile.json
```

Устаревшая папка brainbox/pipelines удалена вместе с её обёртками. Makefile отсутствует.


Controller staging копирует canonical runtime в generated build context app/wakeword_core. Generated copy не коммитится и проверяется по source identity. Core не импортирует Chara/host orchestration; это проверяется import test. Регистрация decider добавляется только в существующие экспорты voice_analysis и принятую discovery-схему.

Документы: plan.md, research.md, data-model.md, contracts/pipelines.md, contracts/dataset.md, contracts/decider.md, quickstart.md. tasks.md создаётся следующим этапом, здесь не создаётся.

## Phase 0 — Research

[research.md](research.md) фиксирует реальные образцы voice_train/piper_training/paraphrasing, FileLike transport, ограничения builder и недостающую гарантию обычного brainbox_training_pipeline при lost response. Все решения приняты, открытых NEEDS CLARIFICATION нет. Не переносить destructive reset из PiperTraining и не предполагать, что builder автоматически копирует brainbox/chara.

## Phase 1 — Design and execution order

1. Изолировать лёгкие contracts/settings/archive IO и вычислительный core от Chara. Сохранить regression baseline модели, sampling, schedules, checkpoint selection, final ORT metrics. Комментарии JSON не участвуют в fingerprint.
2. Перенести generation в brainbox с lazy imports. Оставить Chara.call имена существующих стадий и durable batch logic; адаптер старого manifest собирает portable features-only dataset с теми же hashes и lineage, без TTS.
3. Реализовать валидацию входа в два слоя: хост проверяет ZIP/layout/hash/header/count/provenance и bounded finite float32 scan через stdlib; сервер повторяет всё через NumPy mmap до optimizer. Проверка target — проверка metadata/lineage, не повторный ASR.
4. Создать WakewordTraining controller/installer/image с отдельным lock и ACAV resource profile. Установка скачивает фон и строит manifest; readiness не доверяет одному installation.yaml. Train не устанавливает недостающие ресурсы автоматически.
5. Server stages: receive_dataset -> validate_dataset -> bind_background -> training -> selecting -> exporting -> evaluating -> reporting -> package_result. Каждый этап — метод/компонент; compute не знает путей хоста.
6. Host training stages: validate_source -> prepare_archive -> validate_remote_ready -> persist_request -> submit_or_reconcile -> follow_training -> export_result -> download -> verify_result -> publish. Стабильная идентичность сохраняется до submission; повтор не создаёт новое обучение при неизвестном статусе.
7. Отделить server completion manifest (включает PT/checkpoints) от portable result manifest (только выгружаемые файлы). Оба отчёта пересобираются на хосте без PT/BrainBox/torch/ORT. Download не удаляет серверный run автоматически.
8. Перенести check/setup/run обязанности Make в Python Chara entry points. Удалить Makefile, исправить README/config/comments/старые wrappers; конфиги smoke/full остаются явными, без незаметного выбора smoke.
9. Пройти contract/regression/native CPU/Docker/remote/fault tests и полный рабочий прогон, записать реальные числа в validation.md во время реализации. Нет декларации готовности по mock-only тесту.

## Validation gates

- FR-001–005, SC-001: независимая генерация, Parler/Vosk неизменны, 3N/review, batching, все четыре NPY, feature-only ZIP, old-output repack без синтеза.
- FR-006–011, SC-003/004: installer idempotence/hash failures, source/profile compatibility, host и server checks, no raw/audio/background payload, отсутствие mount локального диска, небезопасный ZIP отвергается.
- FR-012–016, SC-002/005: реальный Linux CPU update/ONNX/ORT parity, final scores, английский/русский отчёты, экспорт без PT, офлайн rebuild после удаления доступности сервера/checkpoints.
- FR-017–021, SC-006/007: отдельные Python команды, scoped dependencies, no Chara import cycle, lost submission response, interrupted optimizer/new output, completed trainer/late failure reuse, lost download no retrain, output locks и fingerprint mismatch.
- SC-008: full curriculum на реальном доступном корпусе, actual counts/bytes/time/RSS и ограничения качества; если корпус мал, это явно обозначается. Проверить Ruff и mypy для перемещённых модулей и весь существующий тестовый набор.

## Complexity Tracking

Нарушений конституции нет. Новый decider обязателен по запросу; portable manifests и отдельная durable submission нужны для удалённой машины и восстановления без повторного обучения. Общая база/новый транспорт/framework не добавляются.

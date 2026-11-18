# Research: два пайплайна и удалённый WakewordTraining

Дата: 2026-11-17. Исследование исходного кода, без изменения runtime.

## 1. Соседние Chara-пайплайны

**Decision**: Оркестрация в chara/wakeword, Chara импортируется лениво. GenerationPipeline и TrainingPipeline показывают именованные этапы через Chara.call; IO, валидация и вычисления вынесены в отдельные компоненты.
**Rationale**: chara/voice_clone/common/voice_train/pipeline.py отделяет подготовку от remote tasks; chara/voice_clone/distillation/training/training_and_export.py отделяет обучение от export/download. chara/paraphrasing/common/paraphrase_pipeline.py делает основной поток читаемой последовательностью компонентов. Размещение в brainbox — явное требование пользователя, хотя образцы находятся в chara.
**Alternatives considered**: оставить основной код в chara/wakeword (против требования); импортировать Chara в brainbox/__init__.py (цикл brainbox → chara → brainbox); переносить все детали в один __call__ (против требования читаемости).

## 2. Dataset и результаты

**Decision**: Следовать PiperTraining: train(..., dataset: Iterable[bytes] | FileLike) с websocket progress и отдельный export(result_reference) -> FileLike. На хосте dataset — Path ZIP; сервер пишет поток через FileLikeHandler. Выгрузка результата — отдельный ZIP через result_to_file/cache streaming.
**Rationale**: brainbox/deciders/voice_generation/piper_training/app/interface.py, app/service.py и chara/voice_clone/distillation/training/training_and_export.py уже используют этот путь. chara/common/pipelines/brainbox/brainbox_training.py получает небольшой финальный DTO из JSONL результата, не весь архив в памяти.
**Alternatives considered**: общий bind mount (не работает между машинами); ручной новый HTTP upload API (не нужен); чтение больших ZIP через cache.read целиком (лишняя память).

## 3. Устойчивость обучения

**Decision**: Заимствовать стиль и progress format общих helpers, но добавить в новый pipeline стабильные task_id/training_id до отправки и reconciliation. Новый decider хранит fingerprint и server state; экспорт повторяется отдельно от train. Общие fundamental helpers не менять.
**Rationale**: brainbox_training_pipeline вызывает api.add внутри Chara-фазы. Потеря ответа до сохранения ID не гарантирует отсутствие дубликатов. Текущий wakeword/generation/brainbox_execution.py уже решает похожую проблему стабильными ID; его пакетную логику генерации сохраняем.
**Alternatives considered**: слепое повторение api.add или Piper continue_existing=False с удалением каталога — нарушает FR-019/020. После partial optimizer loop требуется новый training_id/output. После завершённого trainer повторяет только selecting/export/evaluate/report/download.

## 4. Переносимый вход

**Decision**: Dataset ZIP schema v1 содержит ровно manifest.json и четыре NPY признаков. Без WAV, review, ACAV, melspectrogram/embedding файлов и абсолютных путей. Manifest связывает feature rows с lineage/accepted original counts и preparation identity. Generation остаётся прежней, затем строится дополнительный portable manifest.
**Rationale**: ответы A/C пользователя; существующий training/inputs.py ожидает resources.json и локальные пути — его нельзя использовать как удалённый контракт без adapter. Нельзя пересчитывать аугментации на сервере: они уже вошли в признаки.
**Alternatives considered**: WAV+features (лишняя передача); WAV-only (изменение границ этапов); перенос исходного resources.json без адаптации (утечка непереносимых путей).

## 5. Постоянный фон и совместимость

**Decision**: Установка WakewordTraining готовит ACAV train/validation в /resources/background, проверяемый resource manifest и версии feature space. Ресурсный recipe закрепляет source revision/hash и алгоритм выделения частей: первые floor(N/10) строк — train, следующие floor(N/100) — validation, validation flatten с сохранением T/границ строк; как generation/local/resources.py. Resource ID и hash source/slicing/feature-space обязательны. Готовые признаки принимаются только с совместимым feature-space ID. Конкретный ACAV source revision и recipe едины между generation profile и installer; несовпадение фона при повторе требует новый run.
**Rationale**: ACAV постоянно переиспользуется, синтетические негативы принадлежат корпусу. Начальная установка может потребовать исходный большой NPY, рабочие подмножества сохраняются; readiness проверяет файлы и хеши, не только installation.yaml.
**Alternatives considered**: передавать ACAV в каждом ZIP (запрещено); скачивать фон при каждом train (медленно, невоспроизводимо); загружать FMA/MITRIR в training image без использования (не нужно: генерация уже выполнила аугментации).

## 6. Image и вычислительное ядро

**Decision**: Стандартный DockerMarshallingController, Installer, app/main.py, interface/api/settings/controller/run как у соседних decider-ов. Чистое ядро без Chara/host path хранится в brainbox/deciders/voice_analysis/wakeword_training/runtime. Controller через существующий deployment build context копирует канонический core в staging app/wakeword_core; исходники не дублируются вручную. Проверка содержимого image — обязательный gate.
**Rationale**: BrainboxImageBuilder копирует app/ и foundation_kaia, но не весь brainbox/chara. Импорт chara.wakeword.training из контейнера не заработает. Нельзя править framework ради одного image.
**Alternatives considered**: Chara внутри контейнера (лишняя зависимость); две независимо поддерживаемые копии trainer (риск расхождения); глобальное изменение builder (не требуется).

## 7. Зависимости и рецепт

**Decision**: Базовый Linux Python 3.11 CPU image: torch 2.2.2+cpu, NumPy 1.26.4, ONNX 1.16.1, ORT 1.17.3, Matplotlib 3.9.2 плюс явно закреплённые зависимости runtime. Отдельный серверный lock, не полный host audio lock. Сборка/проверка Linux wheel compatibility — задача реализации, не уже пройденный тест. Requested cuda при отсутствии CUDA даёт отказ; гарантированная приёмка — CPU, auto разрешается в CPU. GPU-image не является обязательным отдельным результатом feature.
**Rationale**: минимальный перенос существующего проверенного алгоритма; не использовать Torch/Python версии PiperTraining автоматически. Базовый builder ставит pip/wheel/setuptools; требуемые build backends описывать явно, не повторять прежний flit_core сбой.
**Alternatives considered**: обновление модели/библиотек вместе с миграцией (усложняет сравнение); Linux image с Windows-only host lock (непереносимо).

## 8. Локальная проверка и отчёты

**Decision**: Хост training-only использует stdlib для ZIP/hash/header/finite checks и проекта kaia для API; не импортирует torch/ORT/audio stack. Float32 payload сканируется ограниченными чанками через array/struct и math.isfinite с учётом byte order; сервер повторяет полную chunked проверку finite/dtype через NumPy mmap до update. Локальный report-only использует NumPy/Matplotlib без torch/ORT/inference. Отдельный export-manifest перечисляет только реально выгруженные файлы, не PT checkpoints/last-trained/final-state.
**Rationale**: текущий reporting.verified_sources проверяет server completion hashes, включающие PT; перенос этого marker на хост потребовал бы лишние checkpoints. Разные internal completion и portable export manifests устраняют это противоречие. На хосте проверяется заявленное слово в provenance; повторное распознавание аудио без WAV невозможно и не обещается.
**Alternatives considered**: скачивать все checkpoints (отклонено пользователем); отчёты только на сервере (против локальной пересборки); full finite scan Torch на хосте (против training-only без ML).

## 9. Миграция интерфейса

**Decision**: Основные новые entry points — python -m chara.wakeword.scripts.generate / train / prepare / report. Makefile удаляется. Конфигурации остаются в chara/wakeword на переходном этапе; команды принимают явный config path. Старые Python generation entry points становятся тонкими deprecated re-exports; старый full run не запускает host training, а делегирует новой remote orchestration. Единственный поддерживаемый trainer — decider core. Старые совместимые generation outputs можно упаковать без TTS.
**Rationale**: два независимых pipeline, сохранение доступности пользовательских данных и отсутствие двух расходящихся реализаций.
**Alternatives considered**: оставить Make как обязательную оболочку; молча трактовать старый generation output как training output; мигрировать старое host-trained PT состояние в новый Linux run (небезопасно, не требуется).

## Итог

Архитектурные неопределённости разрешены по исходному коду и ответам пользователя. Runtime/Docker/remote проверки остаются будущими gate реализации. Новый сервис нужен только для обучения; framework BrainBox и соседние пайплайны не изменяются.

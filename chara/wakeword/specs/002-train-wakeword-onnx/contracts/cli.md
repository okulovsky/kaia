# CLI и публичный API

Контракт команд feature 002; фактические проверки реализации перечислены в ../validation.md.

## Make (cwd = chara/wakeword)

Общие параметры: PYTHON=python, BRAINBOX_URL=http://127.0.0.1:8090, CONFIG=settings/minimal.json, TRAIN_CONFIG=learn-settings.json, OUTPUT, DATASET optional. Scope: generation/training/full. Относительные пути CONFIG/TRAIN_CONFIG и DATASET/OUTPUT передаются относительно cwd; пути внутри JSON разрешаются относительно соответствующего JSON.

| Команда | Назначение | Нужен BrainBox |
|---|---|---|
| make check SCOPE=full | Проверить generation prerequisites и обучение/экспорт, ничего не устанавливать | Да для generation |
| make setup SCOPE=full | Подготовить недостающие зависимости/ресурсы/модели, сохраняя стандартный API установок | Да для generation |
| make generate CONFIG=… OUTPUT=… | Прежняя подготовка данных, результат OUTPUT/dataset | Да, если требуются новые генерации |
| make train DATASET=… TRAIN_CONFIG=… OUTPUT=… | Обучить на готовых данных, экспортировать и сформировать отчёт | Нет |
| make run CONFIG=… TRAIN_CONFIG=… OUTPUT=… | Полный цикл, результат включает модель и отчёт | Да, если нужны новые данные |
| make run DATASET=… TRAIN_CONFIG=… OUTPUT=… | Полный training/export/report цикл с существующим датасетом, без генерации | Нет |
| make report OUTPUT=… | Восстановить отчёт из сохранённых результатов обучения | Нет |

DATASET обязателен для train и может указывать на generation root (с dataset/manifest.json) либо непосредственно dataset/ с соседним resources.json; resolver однозначно определяет root и проверяет согласованность. Bare NPY без manifest не принимаются. Нестандартные ACAV inputs можно передать через --background-manifest с полным provenance/segment lengths; отсутствие обязательного фона не исправляется автоматической загрузкой в train.

SCOPE=training проверяет только локальный training/export стек и, если DATASET задан, проверяемые training inputs; не требует Parler/Vosk, FFmpeg или фоновых WAV для аугментации. SCOPE=generation сохраняет проверку подготовки данных. SCOPE=full объединяет их. Установка training dependencies использует совместимые pinned версии существующего host lock с добавленным ONNX; импортированный DLL не заменяется pip в том же живом процессе Windows. Сам проект kaia остаётся prerequisite активного окружения.

По умолчанию make run выполняет полный цикл с основными настройками learn-settings.json; старое data-only поведение доступно как generate. Короткий прогон выбирается явно через TRAIN_CONFIG=settings/training-smoke.json. CONFIG не используется для повторной генерации при заданном DATASET; описание данных берётся из его snapshot.

## Python CLI

- scripts/train.py --dataset PATH --config TRAIN_CONFIG --output TRAINING_OUTPUT [--background-manifest PATH]
- scripts/report.py --output TRAINING_OUTPUT
- scripts/manage.py run --config GENERATION_CONFIG --training-config TRAIN_CONFIG --output FULL_OUTPUT [--dataset PATH]
- scripts/manage.py check/setup --scope generation|training|full --config GENERATION_CONFIG --training-config TRAIN_CONFIG [--dataset PATH]
- scripts/manage.py generate --config GENERATION_CONFIG --output GENERATION_OUTPUT

TRAINING_OUTPUT — каталог обучения с model/report/metadata. FULL_OUTPUT содержит generation/ (если генерировали здесь), training/ и full-run.json. При DATASET external ссылка на него записывается в full-run.json; исходные файлы не копируются и не изменяются. Одинаковый OUTPUT старого generation run не превращается неявно в full output: выбрать новый каталог.

## Public library API

- Существующие GenerationSettings, WakewordPipeline, generation.run(settings,output) и root run сохраняют data-only контракт ради совместимости.
- Добавляются lazy exports TrainingSettings, run_training(dataset,settings,output,background_manifest=None), run_full(generation_settings,training_settings,output,dataset=None), render_training_report(output).
- run_training не обращается к BrainBox и не вызывает generation.run. Проверяет config/data fingerprint до Chara cache; возвращает TrainingResult с путями ONNX/HTML/metrics и отдельным статусом.
- run_full либо переиспользует явно заданный датасет, либо вызывает generation.run в FULL_OUTPUT/generation; затем run_training в FULL_OUTPUT/training. Full status не наследуется автоматически из generation result.
- render_training_report читает только сохранённые артефакты и хеши, возвращает путь report.html; не вызывает train, export или inference.

## Ошибки и повтор

Код 0 означает complete именно запрошенной операции. Код 1 — неготовность/сбой/несовместимость; код 2 — неверные CLI аргументы. Check ничего не устанавливает и показывает категорию проблемы. Make выводит ненулевой код при отказе вложенной команды, даже если его собственное числовое значение отличается.

Сообщение содержит этап и причину. Нет успеха при пустом наборе, zero optimizer updates, NaN/Inf, невозможном экспорте, parity failure или отсутствии отчёта. Существующий complete проверяется по хешам без update/inference. Отсутствующий HTML можно восстановить; повреждённые модель/scores/history требуют разбирательства, не скрытого обучения.

При частичном optimizer loop автоматического resume нет: сохранить partial и предложить новый OUTPUT. При сбое после законченного training stage повтор переиспользует проверенное последнее обученное состояние, checkpoints и уже готовые результаты следующих стадий; выполняются только оставшиеся этапы без новых optimizer updates. Несовпадение config/data/backend/versions требует нового OUTPUT, без перезаписи прежнего. Выходной каталог защищён от параллельной записи.


Для make report OUTPUT указывает именно TRAINING_OUTPUT; после полного запуска это FULL_OUTPUT/training. При run с DATASET применяется training-scope preflight, поэтому отсутствие работающего BrainBox не мешает обработке готовых данных. Полностью завершённый compatible full run проверяется до повторного запуска generation.

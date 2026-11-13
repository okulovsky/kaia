# Quickstart validation: обучение → ONNX → отчёт

Команды train/report и training-конфигурации реализованы. Результаты фактических прогонов и ограничения окружений перечислены в [validation.md](validation.md).

## Предварительные условия

Активное окружение kaia, Python 3.12/Windows для основного smoke, CPU; установленный согласованный host/training стек. Готовый результат генерации feature 001 с четырьмя NPY, manifest и доступными ACAV train/validation ресурсами. Нет необходимости повторно генерировать аудио. Порог default 0.5, для теста используется явно короткий режим [8,4,4] sampling iterations.

Все команды Make ниже — из chara/wakeword. Формат контрактов: [CLI](contracts/cli.md), [артефакты](contracts/artifacts.md), [сущности](data-model.md). TRAIN_CONFIG paths внутри JSON разрешаются относительно JSON; DATASET/OUTPUT относятся к cwd.

## 1. Подготовить только обучение

```powershell
make setup SCOPE=training
make check SCOPE=training DATASET=../../temp/wakeword/test-host-001 TRAIN_CONFIG=settings/training-smoke.json
```

Ожидание: готовы локальные torch/ONNX/ORT/renderer и проверенные inputs. Команды не требуют работающего BrainBox и не устанавливают его модели. Отсутствие или изменение ACAV files, неизвестная сегментация/временная база либо неверный supervised manifest дают явную ошибку, не запускают обучение и не скачивают недостающее скрыто. При несовместимых зависимостях используется отдельная pip/preflight фаза, а не замена загруженной DLL в живом Python.

## 2. Обучить готовый тестовый датасет

```powershell
make train DATASET=../../temp/wakeword/test-host-001 TRAIN_CONFIG=settings/training-smoke.json OUTPUT=../../temp/wakeword/train-smoke-001
```

Проверить:

- Есть минимум одно настоящее обновление весов и события валидации; нет скрытых двух стадий по 2000 steps.
- model_name.onnx, report.html, metrics.json, history.jsonl, data-snapshot.json, selection/export checks и completed manifest находятся в TRAINING_OUTPUT.
- ONNX загружается и исполняется для batch=1 и >1, выдаёт (B,1) в [0,1]; checker/parity пройдены.
- В отчёте сначала final validation metrics, затем кривые, затем данные. На маленьких наборах recall/precision могут быть низкими: числа реальны, не заменены демонстрационными.
- Scores принадлежат итоговому ONNX, метрики пересчитываются из них; background count/exposure и подпись оконного FP/hour присутствуют, waveform duration не выдумана.
- Actual rows берутся из NPY, а не counts×augmentation_rounds; target/source/split hashes связаны с используемым датасетом.

Автоматические численные и сценарные проверки (будущие тесты реализации):

```powershell
python -m unittest discover -s tests -p "test_training_*.py" -v
python -m unittest discover -s tests -p "test_full_pipeline.py" -v
python -m unittest discover -s tests -v
```

Использовать детерминированные fixture scores для точных unit expectations, но не выдавать их за результаты рабочего обучения. Native integration выполняет реальные update/export/ORT. Проверки должны включать no-checkpoint fallback, averaging и повторное final evaluation, off-by-one L=16 → 1 window, запрет окон через границы сегментов, undefined precision и конечность.

## 3. Повтор и восстановление отчёта

Повторить make train с теми же параметрами. Проверить неизменность hash ONNX, числа optimizer updates, истории и синтезированных WAV; повтор не вызывает BrainBox.

В копии завершённого TRAINING_OUTPUT удалить только report.html и выполнить:

```powershell
make report OUTPUT=../../temp/wakeword/train-smoke-report-copy
```

Ожидание: HTML восстановлен, итоговые числа совпадают с metrics/scores, модель и история не изменены; не выполнены training/inference. Без scores либо с повреждённой моделью report-only отказывает с причиной вместо правдоподобного отчёта.

Изменить threshold/seed/stage_steps в копии конфигурации, сохранив прежний OUTPUT: ожидается отказ до update. Повредить копию NPY/ONNX: ожидается явная диагностика, не скрытое переобучение. Прервать optimizer loop: partial checkpoint/history сохраняются, status не complete; повтор явно требует новый OUTPUT, поскольку автоматический optimizer resume вне первой версии.

## 4. Полный цикл

С готовыми данными, без новой генерации:

```powershell
make run DATASET=../../temp/wakeword/test-host-001 TRAIN_CONFIG=settings/training-smoke.json OUTPUT=../../temp/wakeword/full-cycle-smoke-001
```

Ожидание: FULL_OUTPUT/training содержит ONNX и report.html, full-run.json отмечен complete только после всех проверок. Ссылка на внешний dataset сохраняется, исходные данные не меняются. Generation complete не подменяет full complete.

С новой генерацией (BrainBox нужен только для неё):

```powershell
make setup SCOPE=full
make run CONFIG=settings/minimal.json TRAIN_CONFIG=settings/training-smoke.json OUTPUT=../../temp/wakeword/generated-trained-smoke-001
```

Ожидание: generation/ содержит прежние результаты подготовки, training/ — модель/отчёт, корневой full-run.json связывает этапы. Повтор не добавляет TTS и optimizer updates. Старое data-only поведение доступно как make generate.

## 5. Полный рабочий прогон

```powershell
make train DATASET=<готовый-полный-generation-output> TRAIN_CONFIG=learn-settings.json OUTPUT=../../temp/wakeword/train-full-001
```

Зафиксировать фактические размеры/хеши наборов, seed, policy versions, шаги/updates, длительность, peak memory с методикой, selection/fallback, parity, финальные метрики и путь ONNX. Проверить всё число validation окон партиями. Не обещать определённый recall/FAR и не называть validation независимым тестом, поскольку она использовалась для selection. Ограничения диска/оборудования и невыполненные проверки записывать явно в будущий validation.md.


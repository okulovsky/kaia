# Проверка реализации обучения, ONNX и отчёта

Дата: 2026-11-10. Проверено на Windows 11, CPU. Числа ниже получены из сохранённых артефактов, а не из настроек желаемого результата.

## Окружения

- Основное: `D:/Anaconda/envs/wakeword/python.exe`, Python 3.12.16; torch 2.2.2+cpu, NumPy 1.26.4, ONNX 1.16.1, ORT 1.17.3, Matplotlib 3.9.2.
- `.staging/venv312`: отдельный venv с `--system-site-packages` существующего окружения kaia/wakeword. Установка `pip install --no-deps --prefer-binary -r requirements-host.lock.txt` завершилась. Это проверка установки поверх существующего проекта, не заявление о полностью чистом окружении без kaia.
- `.staging/venv311`: отдельный venv Python 3.11.16 поверх kaia/BrainBox-окружения, без изменения его пакетов. Установлены закреплённые пять библиотек обучения. `pip install --dry-run --no-deps --prefer-binary -r requirements-host.lock.txt` разрешил весь host lock для 3.11; полный audio stack в этом venv не устанавливался. Native обучение, ONNX и отчёт проверены тестами; генерация аудио на Python 3.11 здесь не проверялась.
- Проверки setup выполняются в дочернем процессе до pip; загруженные DLL не заменяются внутри процесса preflight. Исходный код framework/deciders BrainBox не менялся.

## Реальный smoke на готовом датасете

```powershell
python scripts/train.py --dataset ../../temp/wakeword/test-host-001 --config examples/training-smoke.json --output ../../temp/wakeword/train-smoke-002
```

Результат: `kaia/temp/wakeword/train-smoke-002/`, status complete. Четыре supervised массива имеют фактическую форму `(2,16,96)` каждый. Фон: train `(562500,16,96)`, validation `(900000,96)`, исходные сегменты длиной 16. Оценено ровно 56 250 допустимых окон; окна через границы исключены. Знаменатель — 900 000 кадров × 0.08 с = 20 эквивалентных часов признаков; длительность исходного waveform неизвестна.

Выполнено 16 sampling iterations и 16 optimizer updates, три стадии; время самого trainer — 15.188 с. ONNX загружен и исполнен ORT, dynamic batch проверен; максимальная абсолютная parity error — `1.2665987014770508e-7`. Допуск: `1e-5 + 1e-4*abs(reference)`.

## Полный curriculum на малом настоящем датасете

```powershell
python scripts/train.py --dataset ../../temp/wakeword/test-host-001 --config examples/training-full.json --output ../../temp/wakeword/train-full-002
```

Результат: `kaia/temp/wakeword/train-full-002/wakeword.onnx`, `report.html`, complete manifest и все первичные результаты. Новый синтез не выполнялся.

| Стадия | Sampling iterations | Реальные updates | Итерации без retained examples |
|---|---:|---:|---:|
| 1 | 20000 | 4072 | 10915 |
| 2 | 2000 | 1 | 1991 |
| 3 | 2000 | 1 | 1992 |
| Всего | 24000 | 4074 | 14898 |

Некоторые итерации сохраняют менее accumulation_examples примеров и не делают отдельного update; остаток сбрасывается до последней валидации каждой стадии. В history записано 4074 настоящих loss/update и 60 validation events. Отобраны и усреднены 58 кандидатов; fallback не понадобился. Максимальная абсолютная parity error — `7.194466888904572e-8`.

Время trainer — 261.281 с. Весь дочерний Python-процесс — 332.469 с. Пик RSS — 2 266 537 984 байт (около 2.11 ГиБ), замер psutil каждые 0.2 с. Scope включает импорты kaia, хеширование/проверку mmap, обучение, ORT и отчёт. RSS включает резидентные страницы файлов; это не измерение исключительно памяти модели и не SLA. Массив всех перекрывающихся окон не создаётся, на device передаются только партии. Проверка конечности ограничена чанком 262144 элементов, включая Fortran-order NPY.

## Фактические итоговые метрики

Для обоих реальных запусков итоговый ONNX дал TP=0, FP=0, TN=2, FN=2: recall=0, precision=null (`TP+FP=0`), F1=0, accuracy=0.5. На фоне 0 положительных окон из 56250, показатель 0 пороговых окон/ч признаков. Это слабый классификатор на крайне малом наборе; нулевая фоновая метрика не доказывает полезность модели. Результаты не выдаются за production quality или независимый тест обобщения.

В report сначала показаны эти метрики, затем фактические loss/validation curves, затем snapshot данных. Графики — встроенный SVG, без CDN; строки экранированы; неизвестные duration/speaker identities не заменяются нулями. Проверки пересчитывают показатели из сохранённых scores и связывают их с SHA-256 ONNX.

## Команды, повтор и сбои

Фактически завершились с кодом 0:

- `make setup SCOPE=training PYTHON=D:/Anaconda/envs/wakeword/python.exe`;
- `make check SCOPE=training DATASET=../../temp/wakeword/test-host-001 PYTHON=D:/Anaconda/envs/wakeword/python.exe`;
- `make run DATASET=../../temp/wakeword/test-host-001 OUTPUT=../../temp/wakeword/full-smoke-002 PYTHON=D:/Anaconda/envs/wakeword/python.exe`;
- `make report OUTPUT=../../temp/wakeword/train-smoke-002 PYTHON=D:/Anaconda/envs/wakeword/python.exe`;
- повторный `make train ... TRAIN_CONFIG=examples/training-full.json OUTPUT=../../temp/wakeword/train-full-002`.

Повтор smoke и отдельный report CLI дали коды `[0,0]`. SHA-256 history, ONNX и трёх scores файлов до/после совпали (`.staging/repeat-proof.json`). Никаких новых optimizer updates или synthesis calls; report-only тест запрещает вызовы Adam и InferenceSession. Fault injection проверяет selection, export, evaluation и report: завершённый trainer не вызывается повторно. Прерывание optimizer loop требует новый output, новый запуск использует прежний датасет. Отдельно проверены lock, fingerprints, повреждённые ONNX/metrics/history и отсутствие только HTML.

## Автоматические проверки

Команды и сохранённые логи:

```powershell
python -m unittest discover -s tests
.staging/venv311/Scripts/python.exe -m unittest discover -s tests -p "test_training_*.py"
```

Точные итоговые количества и exit codes после последней регрессии фиксируются ниже. Native тесты выполняют настоящее обучение/экспорт; числовые fixture являются синтетическими тестовыми входами и не используются как доказательство качества. Старые generation tests используют свои stub API; их сообщения upload не означают новый реальный синтез.

## Покрытие требований

| Требования | Реализация и доказательство |
|---|---|
| FR-001–004, SC-001 | training package, smoke/full settings, реальные smoke/full прогоны, make train/run |
| FR-005–006 | inputs hashes/shape/finite/lineage/provenance, mmap и segment iterator; invalid input и bounded scan tests |
| FR-007–008 | update/validation/stage_end history, candidate index, selection/averaging/fallback tests |
| FR-009–010, SC-005 | checker + ORT batch 1/>1, parity, тесты отказа без публикации ONNX |
| FR-011–012 | final ORT scores, confusion counters, exact numerical metrics tests, явные frame/exposure/segmentation |
| FR-013–017, SC-003–004 | report order/SVG/escaping, recomputation, SHA identity, offline rebuild/no inference tests |
| FR-018–020, SC-002/006 | final manifest последним, output lock/fingerprint, partial restart и четыре late failure recovery tests |
| FR-021 | scoped check/setup, совместимый data-only Python API, make generate/train/run/report, регрессия генерации |
| SC-007 | полный curriculum, actual counts/updates/time/RSS и явное ограничение малого датасета выше |

## Отличия от исходного ноутбука

Окна строятся внутри исходных сегментов с числом L-16+1. Нет полной копии ACAV/sliding windows на device. Непустой накопленный остаток применяется до завершающей валидации. Loss отражает только настоящий optimizer.step. Итоговые метрики измерены на экспортированном усреднённом ONNX, а не взяты из последнего validation event или среднего checkpoints. Побитная воспроизводимость между версиями Python/платформами не обещается.

## ???????? ?????????

- Python 3.12.16: 69 tests, OK, ??? skipped; ??? `.staging/py312-verified.log`.
- Python 3.11.16: 28 native training tests, OK, ??? skipped; ??? `.staging/py311-verified.log`.
- ??????? ??????????? ????? subprocess ? ??????????? ??????????? return codes ? `.staging/test-returncodes.json`; ?????????????? ????????? ?? ???????????????? ??? ????????? ??????.
- ??????????? ????????? `brainbox/deciders/voice_analysis/vosk/app/service.py` ??? ?????????? ? ??????? ?????? ? ?? ???????????? ???? feature.

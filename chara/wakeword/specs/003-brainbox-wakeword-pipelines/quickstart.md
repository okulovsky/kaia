# Quickstart validation: generation -> ZIP -> remote training -> local results

Команды feature 003 реализованы. Фактические проверки и ограничения записаны в validation.md: наличие команды не означает, что контейнерная и удалённая приёмка уже выполнена.

## Prerequisites

- Актуальный установленный kaia/brainbox на сервере и хосте, совместимая версия protocol/schema.
- На сервере: Docker, достаточно места для ACAV source/подмножеств, image и training runs; серверный /resources не принадлежит хосту.
- На хосте генерации: прежний host audio stack и FFmpeg, доступ к ParlerTts mini-v1/Vosk en через BrainBox. Новых требований генерации к качеству/бюджету нет.
- Для запуска только remote обучения: kaia client, Python 3.11–3.12; torch/ORT/FFmpeg/аудиокорпуса на хосте не требуются. Offline renderer отдельно требует NumPy/Matplotlib.
- Две независимые машины/изолированные filesystem для доказательства remote case. Недостаточно одного локального bind mount общего source directory.

Команды выполняются из корня kaia; далее HOST_GENERATION_OUTPUT и HOST_TRAINING_OUTPUT принадлежат хосту. В примерах URL заменить своим. Сервер запускается из его собственного проекта/окружения:

```powershell
python -m brainbox.run --data-folder D:/brainbox-data
```

На Linux сервере data-folder — его собственный Linux path. Если новый decider не зарегистрирован, обновить серверный проект и перезапустить BrainBox; prepare на клиенте не обновляет удалённый Python-код автоматически.

## 1. Explicit preparation

```powershell
python -m chara.wakeword.scripts.prepare --config chara/wakeword/settings/smoke.json --scope generation --brainbox-url http://SERVER:8090
python -m chara.wakeword.scripts.prepare --config chara/wakeword/settings/smoke.json --scope training --brainbox-url http://SERVER:8090
python -m chara.wakeword.scripts.prepare --config chara/wakeword/settings/smoke.json --scope training --check-only --brainbox-url http://SERVER:8090
```

Проверить: Parler/Vosk готовы, WakewordTraining зарегистрирован, image/service/profile готовы; ACAV находится на сервере. Повтор установки не скачивает verified unchanged files. Отдельно повредить копию ресурса в тестовом sandbox: check отказывает, train не пытается скачать, explicit prepare восстанавливает/диагностирует. Не портить реальные пользовательские ресурсы ради теста.

## 2. Generate small independent corpus

```powershell
python -m chara.wakeword.scripts.generate --config chara/wakeword/settings/smoke.json --output temp/wakeword/remote-gen-smoke-001 --brainbox-url http://SERVER:8090
```

Ожидание: папка с четырьмя feature NPY, source generation metadata/review и dataset.zip; ZIP содержит ровно 4 NPY + portable manifest, без WAV/ACAV/PT. Actual original counts 2 на часть, feature rows проверяются по файлам; 3N/review работают, training job отсутствует. Существующий совместимый batch-smoke-001/generation можно отдельно repack без TTS — migration scenario, не новая генерация.

## 3. Train with no shared host directory

На хосте без Torch/ORT и моделей (с базовыми зависимостями Chara/Avatar, включая NumPy) использовать тот же готовый output (перенос папки/ZIP между хостами допустим), серверу не монтировать его. Expected variants/counts читаются из явной конфигурации:

```powershell
python -m chara.wakeword.scripts.train --config chara/wakeword/settings/smoke.json --dataset temp/wakeword/remote-gen-smoke-001 --output temp/wakeword/remote-train-smoke-001 --brainbox-url http://SERVER:8090
```

Проверить: dataset bytes проходят стандартный FileLike API; server finite checks до update; actual updates/stages записаны. На хосте ONNX, оба HTML, scores/metrics/history/config/snapshot/selection/export-check и portable marker. Нет обязательных PT/checkpoints/background files. ONNX проверен серверным CPU ORT для batch1/>1, parity и диапазона [0,1]; final metrics связаны с ONNX SHA.

## 4. Offline reports

Отключить доступ к BrainBox и исключить доступность серверных checkpoint файлов. Сохранить SHA history/model/scores, удалить только локальные HTML:

```powershell
python -m chara.wakeword.scripts.report --output temp/wakeword/remote-train-smoke-001
```

Оба отчёта восстановлены: validation -> curves -> actual data, без raw JSON dump, внешних CDN или inference. Модель/history/scores неизменны, агрегаты совпадают. Подмена ONNX/scores/history вызывает явный отказ.

## 5. Failures and retries

В автоматизированном sandbox проверить:

- other expected word, недобор original positives, empty/NaN/shape/hash/lineage mismatch, unsafe ZIP -> до update, no successful model marker;
- snapshot extraction остановлено архивным budget -> ресурсов не перезаписано;
- lost response после commit training job -> старый ID найден, не создан второй trainer;
- network unavailable при reconciliation -> transport_unknown, без нового обучения;
- interrupted optimizer -> новый output/ID на том же корпусе, partial сохранён;
- selection/export/evaluation/report failure после verified training -> retry attempt same training_id, update count прежний;
- interruption download -> повтор export/download, no train/TTS, hashes после получения совпадают;
- два concurrent writers -> второй отклонён; incompatible config/resource -> новый output;
- local complete повтор при выключенном сервере -> verified cached success.

## 6. Regression and full recipe

На этапе реализации обновить пути discovery tests для нового package; выполнить весь существующий набор chara/wakeword/tests плюс новые contracts/image integration. Ruff/mypy проверяют новые/перенесённые модули. Контейнерный self-test выполняет настоящее CPU обучение на небольшом числовом fixture без Parler/downloads; отдельный remote smoke использует реальные сгенерированные данные.

Full:

```powershell
python -m chara.wakeword.scripts.generate --config chara/wakeword/learn-settings.json --output temp/wakeword/remote-gen-full-001 --brainbox-url http://SERVER:8090
python -m chara.wakeword.scripts.train --config chara/wakeword/learn-settings.json --dataset temp/wakeword/remote-gen-full-001 --output temp/wakeword/remote-train-full-001 --brainbox-url http://SERVER:8090
```

Если полный корпус уже существует, не генерировать автоматически повторно: repack/reuse проверенные файлы. Зафиксировать actual samples/rows/windows, optimizer updates, selected checkpoints, result/dataset bytes, time/RSS, server versions и final metrics. Полный curriculum на малом наборе явно обозначается; не заявлять production quality. Make не используется ни в одном обязательном сценарии.

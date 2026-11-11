# Проверка локальной архитектуры

Актуальная инструкция: [README](../../README.md). План миграции: [host-migration-plan.md](host-migration-plan.md). Выполняйте команды из chara/wakeword в окружении kaia.

```powershell
make check
make setup
make run CONFIG=examples/minimal.json OUTPUT=../../temp/wakeword/smoke-host-001
make run CONFIG=examples/full.json OUTPUT=../../temp/wakeword/full-host-001
python -m unittest discover -s tests -v
```

BrainBox запускается отдельно из корня kaia: python -m brainbox.run --data-folder "D:/brainbox-data". Нужны только ParlerTTS mini-v1 и Vosk en. WakewordData и Piper не используются. Настройте resource_folder в JSON на диск с достаточным местом; путь относится к JSON. Общие корпуса требуют существенно больше 25 ГБ даже для minimal.

Для проверки настоящей обработки на CPU без загрузок:

```powershell
python tests/native_smoke.py --models <каталог-с-embedding_model.onnx-и-melspectrogram.onnx> --output ../../temp/wakeword-native-host
```

Ожидание: четыре непустых массива (2,16,96), NATIVE_HOST_FEATURES_OK. Тестовые сигналы не являются обучающим корпусом.

Повторите завершённую команду: TTS не должен повторяться. Изменение настроек и старые schema-v1 результаты требуют нового output. Отбраковка сохраняется в review, попытки не сбрасываются, максимум 3N на class/split. Потеря доступа к статусу задания не разрешает новый синтез.

Фактические результаты и оставшиеся проверки: [host-validation.md](host-validation.md).


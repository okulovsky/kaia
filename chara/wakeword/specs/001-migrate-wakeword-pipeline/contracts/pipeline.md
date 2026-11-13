> Host migration 2026-11-08: this document records the prior remote-worker implementation. Current architecture and commands are described in host-migration-plan.md, host-validation.md and ../../README.md. Piper/WakewordData contracts below are historical and removed from runtime.

# Контракты

## Python/CLI
run(settings: GenerationSettings, output: Path) → RunResult — некэшируемая точка входа. Проверяет конфигурацию/артефакты до Chara.start/call. WakewordPipeline имеет __call__.

Планируемая команда из корня kaia:
python -m chara.wakeword.scripts.generate --config path/to/settings.json --output path/to/run

Оба аргумента обязательны. JSON соответствует GenerationSettings. Код 0 только complete. Недобор/сбой: ненулевой код, этап, причина, путь диагностики. Несовпадение настроек требует нового каталога. Повреждённый завершённый артефакт: явная ошибка без скрытого пересчёта.

## BrainBox
Переиспользуются ParlerTts.new_task().voiceover_with_description(text, description, seed=...) и Vosk.new_task().transcribe_to_array(cache_name, model_name).

Будущие методы WakewordData:
- prepare_resources(resource_specs) → manifest;
- generate_negative_texts(target_variants, custom_phrases, seed) → тексты;
- generate_negative_audio(texts, count, seed, resources) → архив WAV/manifest;
- normalize_audio(input_archive, sample_rate=16000) → архив WAV;
- augment_and_extract(input_archive, settings, resources) → четыре NPY/lineage.

Это проектные, пока не существующие методы. Передаются cache names и resource id/revision, не пути другого хоста. Архивы: относительные пути без выхода за каталог. Общий сбой не превращается в пустой успех; ошибки записей содержат sample_id/stage.

## Позитивы
Исходный фильтр слова плюс min(conf) выбранных токенов >= порога. Нет conf, нечисловой или вне [0,1] → review. Пустой срез не вырезается. Границы — середины промежутков соседних слов как VerifierResult.get_audio_cut, на краях начало/конец аудио. Невалидные границы/длительность → review.

## Выходы
settings.json, resources.json, этапы Chara, dataset с четырьмя NPY и manifest, review, report.json. Manifest содержит версии, параметры, происхождение и хеши; публикуется последним. Обработка выбирает accepted manifest, не glob дерева. Бюджет и review сохраняются при resume. Изменение confidence требует нового каталога.


Каждый новый запуск TTS, включая технический повтор после ошибки синтеза, расходует одну попытку из 3N. Чтение существующего задания и повторы Vosk/обработки пригодного аудио не расходуют бюджет синтеза.
Стабильный task_id атомарно сохраняется до сетевой отправки. При восстановлении сначала проверяется задание с этим id: существующее ожидается/читается, подтверждённо отсутствующее отправляется с тем же id. Если проверка недоступна, процесс останавливается с диагностикой без повторного синтеза. Перед реализацией проверяется защита BrainBox от повторной постановки одного task_id.
При поздней отбраковке исходник исключается из accepted, все его производные по lineage_id исключаются из активного manifest, но сохраняются для диагностики. Замена сохраняет class/split и расходует оставшийся бюджет; затронутая группа признаков пересобирается до публикации complete. Недобор запрещает complete.
Уточнение реализации: generate_negative_texts принимает дополнительный count (по умолчанию 100); pipeline передаёт целевой объём группы. Resource kinds: model, piper, mit_rir, background, acav, background_wav, rir_wav. Подготовленный source=file:///resources/... проверяется на worker. Во входном spec sha256 необязателен, фактические хеши и разрешённые snapshot revisions сохраняются в resources.json. При недоборе Python run поднимает IncompleteGeneration и сохраняет report.status=incomplete; CLI возвращает 1. Перед продолжением частичного запуска сверяются установленные голосовые модели; готовый набор проверяется локально без зависимости от доступности BrainBox.

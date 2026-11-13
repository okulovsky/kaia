> Host migration 2026-11-08: this document records the prior remote-worker implementation. Current architecture and commands are described in host-migration-plan.md, host-validation.md and ../../README.md. Piper/WakewordData contracts below are historical and removed from runtime.

# Модель данных

## GenerationSettings
schema_version, name, target_variants, language_code, prefix/suffix, counts для positive/negative × train/test, custom_negative_phrases, seed, batch_size, min_vosk_confidence=0.7, augmentation_rounds/batch_size, resource_specs.
Непустые варианты, безопасное имя, положительные counts/rounds/batch, конечный confidence в [0,1], поддерживаемый язык. Defaults разворачиваются до canonical JSON; версии моделей входят в сравнение. Адрес сервера и журнальные параметры не меняют семантику данных.

## ResourceSpec / ResourceManifest
id, тип, источник, revision, sha256, размер, версия обработки, готовность. Путь worker не является переносимым id.

## AudioCase (ICase)
sample_id, lineage_id, class_label, split, target_variant/negative_text, voice_description, seed, attempt_index, task_ids, source_audio, recognition(word/start/end/conf), verification, crop_audio, normalized_audio, error_stage/reason_code/error.
Состояния: planned → submitted → voiced → recognized → accepted_crop → normalized → processed. Отбраковка → review и новый case с новым seed; технический повтор сохраняет id; общий отказ → failed_run. Негативы не проходят позитивный predicate. Потомки и замены сохраняют class/split.

## GenerationProgress
По class/split: target=N, budget=3N, reserved_attempts, accepted_ids, rejected_ids, pending_task_ids. Атомарное резервирование до отправки; accepted ≤ N, reserved ≤ 3N; resume восстанавливает счётчики. Аугментации не расходуют бюджет исходных WAV.

## ReviewRecord
sample_id, stage, reason_code, expected/recognized_text, доступные confidence/timestamps, voice/seed, исходное аудио и при наличии crop.
Причины: word_not_found, low_confidence, missing_confidence, invalid_crop, invalid_audio, processing_failed.
review/<sample_id>/audio.wav и record.json; без аудио сохраняется метадата. Review не выбирается для датасета.

## FeatureArtifact / RunResult
Четыре NPY: positive_features_train, negative_features_train, positive_features_test, negative_features_test.
shape=(M,16,96), числовой dtype, M>0, finite, sha256, size, lineage manifest. M зависит от upstream augmentation, не приравнивается к N исходных WAV. Совместимость с преобразованием потребителем в float32.
RunResult: complete/incomplete/failed, effective_settings, resource_manifest, progress, feature_artifacts, review_path/report_path. Completed manifest только после полной проверки; недобор не является complete.


Каждый новый запуск TTS, включая технический повтор после ошибки синтеза, расходует одну попытку из 3N. Чтение существующего задания и повторы Vosk/обработки пригодного аудио не расходуют бюджет синтеза.
Стабильный task_id атомарно сохраняется до сетевой отправки. При восстановлении сначала проверяется задание с этим id: существующее ожидается/читается, подтверждённо отсутствующее отправляется с тем же id. Если проверка недоступна, процесс останавливается с диагностикой без повторного синтеза. Перед реализацией проверяется защита BrainBox от повторной постановки одного task_id.
При поздней отбраковке исходник исключается из accepted, все его производные по lineage_id исключаются из активного manifest, но сохраняются для диагностики. Замена сохраняет class/split и расходует оставшийся бюджет; затронутая группа признаков пересобирается до публикации complete. Недобор запрещает complete.
Уточнение реализации: поддерживается language_code=en. Во входном ResourceSpec ожидаемый sha256 необязателен; при наличии это 64 шестнадцатеричных символа. В выходном ResourceManifest фактические SHA и checksum_scope обязательны; для RIR это агрегат хешей подготовленных артефактов, для файлов — SHA исходного файла. Progress хранит список попыток с id/seed/task_id/state/index; accepted/review и остаток бюджета выводятся из него и review. Отчёт недобора имеет status=incomplete, Python run поднимает IncompleteGeneration; успешный run возвращает RunResult.

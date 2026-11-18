# Data model: portable corpus, server run and exported result

## UnifiedConfiguration

`generation` + `training`, отдельные `_comments`. Generation сохраняет name/target_variants/counts, Parler/Vosk confidence, prefix/suffix, seed, batch/augmentation settings и локальный resource_folder. Training сохраняет исходные numeric settings и добавляет expected_target_variants, minimum_positive_counts{train,validation}, server_resource_profile, training_id policy. BrainBox URL относится к окружению подключения, не меняет числовой рецепт.

Expected target/counts по умолчанию берутся из generation section общей конфигурации, но явно разрешаются и фиксируются до train; данные из manifest не подставляются вместо ожидания пользователя. Flat старые конфиги поддерживаются переходными readers, неизвестные поля не игнорируются. Paths внутри JSON относительны самому JSON; generation paths принадлежат хосту, серверные resource paths никогда не вычисляются из них. `_comments` исключаются из canonical/fingerprint.

## PortableDatasetManifest (schema_version=1)

- corpus_id: content-derived ID; status=complete; created_at informational.
- target: name (label), variants (непустые строки), normalized_variants (casefold, whitespace collapse, sorted unique).
- preparation: recipe_version, synthesis_backend=parler-mini-v1, processing_backend=host-v2, prefix/suffix/confidence, seed, augmentation settings, language, source versions.
- feature_space: input shape [16,96], float32, feature extractor revision and model content hashes. Версия preprocessing определяет совместимость с фоном сервера.
- parts: positive_train, positive_validation, negative_train, negative_validation; file, sha256, size_bytes, dtype, actual_shape, feature_rows, accepted_original_count, source_lineage_ids.
- lineage: уникальные sample_id/lineage_id, class и split; исходные original counts считаются по этим записям, а не по config counts или rows. Один lineage не пересекает train/validation.
- generation_summary: фактический review count и краткие причины, без review WAV/records; requested counts отдельно от actual.
- source_manifest_sha256: идентичность исходной папки для audit, но исходный файл не требуется на сервере.

Все четыре части обязательны и непусты; shape=(N,16,96), N>0; header/file size/hash согласованы. Порядок строк NPY сохраняется, преобразование классов/выборок при упаковке запрещено. Текущие имена positive_features_test/negative_features_test сопоставляются роли validation; данные selection не называются independent test. Бинарные данные признаков не меняются при repack; имя файла не является доказательством роли.

## DatasetArchive

file on host; sha256; size_bytes; manifest_sha256; corpus_id; identity of four NPY. Состав — ровно manifest.json и четыре NPY, без WAV/PT/фоновых ресурсов/абсолютных путей. Потоковое создание temporary -> verify -> atomic rename. При переносе не используется generation_root из старого snapshot.

## BackgroundResourceProfile

profile_id/version; source URL/revision/SHA-256; split_recipe (floor(N/10) train, следующие floor(N/100) validation); derived train/validation file hashes and shapes; T, segment counts, frame_step_seconds=.08, feature_space ID, created_versions.

Background train=(N,T,96); validation flattened=(M,96), M%T=0; один исходный row — отдельный validation segment. Все L-16+1 окна, без cross-row окон; evaluated frames и waveform_hours=null. Installer readiness marker хранит profile fingerprint, но при проверке также требуется наличие/хеши файлов. Постоянный фон: /resources/background/<profile_id>/; runs: /resources/training/<training_id>/; отдельные locks и namespaces.

## TrainingRequest

training_id (safe opaque ID), dataset_sha256, portable_manifest_sha256, canonical expected target/minimum counts, canonical TrainingSettings, requested_resource_profile; request_fingerprint. Локально: task attempts{task_id,batch_id,submitted/unknown/finished}, remote result reference, download state. Абсолютный host path служит только локальному IO и не входит в content identity.

Server execution_fingerprint дополняет request identity хешами фактически установленных background artifacts, resolved device и compute versions. Повтор immutable training_id с другими настройками/входами/версией ресурсов отклоняется, существующие файлы не перезаписываются.

## ServerTrainingRun

schema_version, training_id, request/execution fingerprints, received dataset hash, input snapshot, stage statuses, completed stage artifact hashes, current stage, error stage/reason, optimizer_updates, run timestamps, training_complete marker, last-trained/candidate/final-state metadata.

States: receiving -> validating -> training -> selecting -> exporting -> evaluating -> reporting -> complete; failure/interrupted содержит точную стадию. binding/validation включает готовность постоянного фона до первого update.

- Нет завершённого training marker после входа в optimizer: partial сохраняется, нужен новый training_id.
- Есть verified training marker: допустимо завершить selection/export/evaluation/report без updates.
- Complete: повтор train возвращает прежнюю ссылку, export/download не вызывает trainer.
- Running: второй процесс не получает доступ на запись; describe позволяет клиенту наблюдать существующий run.
- received dataset/hash временный; удаление его копии после complete не удаляет background и результат. Автоматическое удаление server result после download не делается.

## TrainingResultReference

training_id, request_fingerprint, execution_fingerprint, status, result_manifest_sha256, archive_sha256, archive_size, model name/hash; ссылка описывает серверный run, а не путь хоста. Передаётся как JSON через финальный BrainboxReportItem.result.

## PortableResultManifest (schema_version=1)

Только обязательные выгружаемые files и их hashes: ONNX, reports, metrics, scores, history, config, data-snapshot, checkpoint-selection metadata, export-check. Есть request/execution fingerprints, dataset manifest hash и background identity. Ни model weights PT, ни checkpoint files, ни background files не являются зависимостями portable marker.

Server completion manifest остаётся внутренним и может ссылаться на PT. Offline renderer проверяет portable marker и recomputes metrics from scores, не загружает PT/ONNX в inference. Серверные checkpoint IDs/hashes в selection — audit metadata, не локальные file references.

## LocalTrainingResult

output, status, remote reference, received archive hash, verified extracted files, report paths, model path, download/verification errors. States: validating_source -> packaging -> checking_remote -> submitting -> following -> exporting -> downloading -> verifying -> complete. Cached complete проверяется до API/network; неполная выгрузка восстанавливается через export/reference. Ошибки сети не превращаются в новое training_id автоматически.

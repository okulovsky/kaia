# Contracts: feature-only dataset and portable result

## Input ZIP v1

Ровно пять файлов:

```text
manifest.json
positive_features_train.npy
positive_features_test.npy
negative_features_train.npy
negative_features_test.npy
```

Файлы — числовые float32 NPY (N,16,96), N>0; allow_pickle=False, hash/size/shape сверяются. Part role test именуется validation в manifest. Без WAV, PT, FMA/MITRIR/ACAV, extractor ONNX, resources.json со старыми absolute paths или review. Manifest содержит поля data-model.md, но не переносит весь directory tree generation.

В manifest требуется accepted_original_count и уникальные lineage IDs по каждой части; количество rows проверяется независимо. Requirements.expected variants совпадают с normalized target set; positive counts >= minimum_positive_counts по обеим частям. Все записи используются, если подходят; surplus не превращается в скрытую выборку. По имени ONNX или generation.name слово не угадывается.

Ограничение переносимого архива: ZIP DEFLATE/STORED, конечный allowlist файлов; без encryption, links, absolute/drive/UNC paths, `..`, duplicate/case-colliding names и nested payloads. До извлечения сверяются cumulative expanded sizes/NPY shape-byte sizes с manifest и настраиваемым archive budget; checksum сам по себе не защищает от zip bomb. Стандартный budget: 2 GiB input expanded/compressed, может быть явно поднят подготовленным профилем. Распаковка в temporary run folder, без перезаписи resources/другого run, атомарное принятие после всех проверок. Во время stream запись также ограничена budget, а не только заявленным ZipInfo.

Архив/манифест имеют content identity; timestamps/host paths не делают новый corpus. Hash файлов проверяется до cache reuse и сервером по фактически полученным байтам. Для full=6000 original samples размер признаков ориентировочно 6000*16*96*4 байт при 1 row на оригинал; это не обещание actual rows после генерации.

## Output ZIP v1

```text
result-manifest.json
<model_name>.onnx
report.html
report_ru.html
config.json
data-snapshot.json
history.jsonl
checkpoint-selection.json
export-check.json
metrics.json
scores/positive_validation.npy
scores/negative_validation.npy
scores/background_validation.npy
```

Только allowlist из portable manifest, без checkpoints/*.pt, last-trained.pt, final-state.pt, training input ZIP, background arrays, Chara caches и внутренних server markers. Server internal completion manifest не копируется как portable completion marker. Размер результата/хеши фиксируются в result-reference; лимит результата настраивается отдельно и проверяется потоково.

ONNX прежнего контракта: opset14, float32 onnx::Flatten_0 [B,16,96] -> output [B,1] sigmoid. Перед export completion checker/ORT CPU batch1/>1, parity atol1e-5 rtol1e-4, final evaluation именно ONNX. Полная валидация, bounded score NPY, временные файлы -> atomic publish. Не переносить старые средние checkpoint metrics вместо final measurements.

Metrics: TP/FP/TN/FN/recall/precision/F1/accuracy, threshold; precision null+reason при TP+FP=0, F1 напрямую. Background window rate = positive_windows/(evaluated_frames*.08/3600), stride1 внутри сегментов, число L-16+1. Waveform_hours=null при неизвестности; это не independent FA/hour.

Перед локальным complete: проверка export-reference/result-manifest hashes, всех файлов, ONNX hash == metrics.model_sha256, snapshot identity, score counts, history actual updates. Локальное получение не делает ONNX inference и не требует torch/ORT. Numerical/report recomputation отдельным лёгким report-only renderer.

Offline report rebuild сверяет portable manifest, пересчитывает агрегаты из saved scores и использует actual history. Неизменяемый result-manifest.json остаётся связан с серверным архивом; хеши двух пересозданных HTML публикуются отдельным local-render.json с source_manifest_sha256. Запрет требовать отсутствующие PT/source dataset/background files. Ни train, ни inference не вызываются. Unknown values имеют причины. Первые разделы: validation -> curves -> dataset, без raw JSON dump; английская и русская версии согласованы по значениям.


Input `corpus_id` hashes canonical manifest content excluding itself. The ZIP uses sorted members and fixed timestamps; `archive_sha256` identifies transport bytes separately. Portable metadata contains no host resource paths. `review_summary` carries aggregate counts/reasons only.

Result reference includes `training_id`, `status`, request/execution fingerprints, result manifest SHA256, archive SHA256/size, model SHA256. The result manifest includes schema_version=1, status=complete, run_id, training_id, both fingerprints and an exact allowlist hash map. Source code identity is included in the numeric engine execution versions/fingerprint.

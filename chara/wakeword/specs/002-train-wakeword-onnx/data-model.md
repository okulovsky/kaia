# Data model: обучение и экспорт wakeword

## TrainingSettings

schema_version=1; model_name (безопасное имя или наследуется из dataset settings); seed; device=cpu/auto/cuda; num_threads; mode=smoke/production; stage_steps[3]; stage_learning_rates[3]; batch_counts{positive,adversarial_negative,background}; accumulation_examples; max_negative_weight; target_window_fp_per_hour; threshold; validations_per_stage; validation_start_fractions[3]; validation_batch_size; export_atol/export_rtol; recipe/selection/background policy versions.

Все counts/steps/batch/threads — положительные целые без bool. LR и веса конечны и положительны; threshold в [0,1]; seed в поддерживаемом диапазоне; три стадии обязательны. Пределы validation и exporter фиксируются в canonical settings. Никаких неявных минимумов 2000 в smoke: stage_steps уже являются фактическими значениями. Requested device и resolved device сохраняются раздельно; недоступная явно запрошенная cuda — preflight failure.

Config paths разрешаются относительно файла конфигурации, CLI dataset/output — относительно cwd. Fingerprint включает разрешённые параметры, входные content hashes, recipe/policy versions и фактические версии вычислительного стека. Изменение входов или параметров не маскируется одинаковой формой файлов.

## DatasetSnapshot

snapshot_id/hash; dataset_manifest_path/hash; generation_root; target_variants/model label; supervised_parts[4]; background_parts; generation_settings; generation resource/source hashes; rejection summary; доступные raw WAV durations и speaker provenance; unavailable_fields{field,reason}.

Supervised part: name, class_label, role=train/validation, file, sha256, size_bytes, actual_shape=(N,16,96), dtype, finite_check, rows=N. Для совместимых готовых данных counts из настроек и lineage описывают исходные записи отдельно от числа строк признаков. Если происхождение не доказано, оно явно unknown; это не разрешает нарушить обязательные manifest/hash проверки.

Background train: file/hash/shape=(N,T,96), N>0,T≥16, finite numeric. Background validation: file/hash/shape=(M,96), segment_count, segment_lengths либо constant_segment_length, hop_seconds=0.08, boundary_source, evaluated_frames, excluded_segments, total_valid_windows, feature_equivalent_hours; waveform_hours optional/null.

Для feature 001 T берётся из проверенной ACAV train части того же источника, segment_count=M/T должен быть целым. Сегменты не пересекают train/validation части. Число окон sum(max(0,L-16+1)); для стандартного ACAV короткие сегменты не допустимы, для импортированного manifest они явно исключаются и не учитываются в exposure. Mapped scores index связан с сегментом/началом окна через сохранённый порядок без миллионов JSON-строк.

## TrainingHistory

JSONL с versioned record types. Общие поля: event_id, timestamp_utc, stage, stage_iteration, global_iteration, optimizer_update, elapsed_seconds.

- update: weighted_bce_loss, learning_rate, negative_weight, accumulated_examples, positive_examples, negative_examples, flush_remainder.
- validation: threshold, positive/negative sample counts, TP/FP/TN/FN, recall, accuracy, background_positive_windows, evaluated_windows, feature_equivalent_hours, window_fp_per_hour, checkpoint_candidate_id optional.
- stage_end: sampled_iterations, optimizer_updates, skipped_iterations, retained_examples, next_negative_weight_max.

Loss появляется только после реального optimizer.step. Несколько validation events могут относиться к одному optimizer_update, но не получают выдуманные update/loss. Непустой accumulation remainder flush-ится до финальной валидации стадии и учитывается как реальный update. Начальные веса и состояния random generators фиксируются seed и версиями; межплатформенная побитная идентичность не обещается.

Нечисловой loss/score вызывает failure, а не молчаливое исключение точки. Повреждённая история завершённого запуска не используется для создания достоверного отчёта. При прерывании сохраняется прочитанный корректный префикс и отдельная диагностика, но не complete.

## CheckpointSelection

Candidate: checkpoint_id/path/hash, stage/global_iteration/optimizer_update, validation_event_id, recall/accuracy/window_fp_per_hour и count. Сохранение кандидатов и их индекса атомарно.

Selection result: policy_version, candidate_ids, percentile_values (p90 accuracy/recall, p10 background rate), selected_ids, tie_break, fallback_reason optional, final_state_path/hash. Пустой пересекающийся отбор → best по FP/hour, recall, earliest event; пустой candidate list → последнее действительно обученное состояние. При усреднении в модели этой feature все state tensors floating; любой новый integer buffer требует явной политики и версии модели, а не автоматического float averaging.

Mean checkpoint metrics могут быть диагностикой, но не final_metrics. Финальная модель имеет отдельную идентичность и отдельный результат валидации.

## ExportCheck

final_state_sha256; candidate_model_file/hash; opset=14; input_name=onnx::Flatten_0; output_name=output; input_dtype=float32; input_shape=(B,16,96); output_shape=(B,1); sigmoid_included=true; structural_check; CPU session load; batch sizes; parity_sample_indices; tolerance{atol=1e-5,rtol=1e-4}; max_absolute_error; parity_passed; finite/range flags; package_versions.

Model file публикуется атомарно только после проверок. Финальная валидация через ORT использует именно hash этого опубликованного файла; замена файла после измерения нарушает совместимость.

## ValidationResult

model_sha256; dataset_snapshot_sha256; threshold; inference_backend=ONNX Runtime CPU; supervised{positive_count,negative_count,TP,FP,TN,FN,recall,precision,F1,accuracy}; background{positive_windows,total_windows,feature_frames,frame_step_seconds,feature_equivalent_hours,threshold_windows_per_feature_hour,window_policy,waveform_hours}; scores_artifacts{path,sha256,shape,dtype,order}; unavailable_values{field,reason}.

Precision: null при TP+FP=0. F1 считается напрямую по confusion counts; отсутствие precision не делает F1 автоматически неизвестным. Фоновая длительность-прокси не подставляется в waveform_hours. Финальные scores конечны и в [0,1]; входной/выходной row count совпадает с snapshot. Validation, использованная для selection, явно помечена и не называется independent test.

## TrainingRun и FullRun

TrainingRun: run_id; canonical_settings; fingerprint; data_snapshot_hash; execution_versions; started/finished_at; stage_status; current_stage; error_stage/reason; outputs и hashes; mode; timing; peak_memory optional с scope/method. FullRun связывает generation_result и training_result и не переопределяет значение generation complete.

Состояния TrainingRun:

```text
new → preflight → training → selecting → exporting → evaluating → reporting → complete
                 ↘ failed(stage) / interrupted(stage)
```

preflight проверяет всё до входа в cache Chara. training завершённым считается только при ≥1 update, истории, законченных стадиях, сохранённом последнем обученном состоянии и индексе кандидатов checkpoints. final-state и selection index формируются следующим этапом selecting; сбой этого этапа не требует новых optimizer updates. Если failure произошёл после training_complete, повтор может продолжить selecting/export/evaluation/report из проверенных артефактов без update. Если optimizer loop прерван, первая версия не продолжает его автоматически: сохраняет partial данные и требует новый output с явным объяснением.

Completion marker публикуется последним и содержит хеши модели, metadata, history, scores и HTML. Проверенный compatible complete переиспользуется. Если отсутствует только HTML, допускается восстановление из сохранённых результатов; повреждение модели/scores/history не исправляется скрытым переобучением. Report-only обновляет HTML и его запись в marker после успешной проверки, а не меняет модель/числа.

## TrainingReport

report.html с version/title/run_id/model SHA; первые секции строго validation_metrics, training_history, dataset_description. SVG встроены; внешних CDN и запросов нет. Metadata описывает hash каждого источника отображаемых чисел. Для unknown duration/speaker count — явная причина, а не 0. Из markdown/названий/путей не допускается внедрение HTML; текст экранируется.


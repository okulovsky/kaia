# Артефакты, метрики и ONNX

## Выход обучения

```text
TRAINING_OUTPUT/
  config.json
  data-snapshot.json
  state.json
  history.jsonl
  checkpoints/index.json
  checkpoints/<checkpoint_id>.pt
  checkpoint-selection.json
  final-state.pt
  <model_name>.onnx
  export-check.json
  scores/positive_validation.npy
  scores/negative_validation.npy
  scores/background_validation.npy
  metrics.json
  report.html
  manifest.json
```

Все path/hash связи описаны в [data-model.md](../data-model.md). PT-файлы — локальные состояния trusted training run; пользовательский произвольный checkpoint не загружается для импорта данных. Числовые NPY читаются без pickle. Новый обязательный file не публикуется пустым success marker. JSON не содержит NaN/Infinity: неопределённые значения — null + reason.

## Input contract

Supervised: четыре непустых конечных числовых массива, формы (N,16,96), роли positive/negative train/validation строго из generation manifest. Для вычисления партия приводится к float32. Original lineages и фактическое число строк сохраняются раздельно. Проверяются хеши всех четырёх файлов, settings/source manifest и ACAV artifact hashes.

Background: train (N,T,96), validation (M,96) + сегменты, или явно импортированные сегменты (K,T,96) с валидированным metadata. Default adapter feature 001 восстанавливает сегментацию из T согласованного ACAV train того же resource item. Нельзя объединять произвольные ACAV train и val только по совпадению формы. Каждый validation segment L≥16 даёт L-15 окон, stride=1; окна через границы исключены. Mapped background scores имеет ровно sum(L-15) элементов и компактный index mapping сегмент → диапазон score indices.

## Итоговые метрики

Положительное решение: score≥threshold, threshold default 0.5.

- TP = число positive scores≥threshold; FN = positive_count-TP.
- FP = число adversarial negative scores≥threshold; TN = negative_count-FP.
- recall = TP/(TP+FN).
- precision = TP/(TP+FP); при нулевом знаменателе null с причиной.
- F1 = 2TP/(2TP+FP+FN); не вычислять через произведение неизвестного precision.
- accuracy = (TP+TN)/(positive_count+negative_count).
- background_positive_windows = число фоновых scores≥threshold, отдельно от FP на adversarial negatives.
- feature_equivalent_hours = evaluated_feature_frames × frame_step_seconds / 3600, default frame_step_seconds=0.08.
- threshold_windows_per_feature_hour = background_positive_windows/feature_equivalent_hours.

Последний показатель подписывается как оконная оценка по времени признаков. Raw count, число окон, exposure, stride, segmentation и отсутствие event grouping обязательны рядом. Если waveform duration неизвестна, waveform_hours=null; название «реальные независимые ложные активации/час аудио» запрещено. Короткие недопустимые сегменты, если импорт разрешает их, исключаются и из окон, и из evaluated frames с явными счётчиками. Полностью нулевой exposure — preflight failure.

Все final scores измерены ORT для хеша опубликованного ONNX. Counters/metrics воспроизводятся из сохранённых scores и snapshot. Метрики validation events в history служат кривым и selection, не заменяют final metrics. Данные selection явно называются validation, а не untouched test.

## Export contract

- ONNX opset 14, один input onnx::Flatten_0, dtype float32, shape [batch,16,96].
- Один output output, shape [batch,1], sigmoid probability, finite, диапазон [0,1].
- CPU execution обязателен; dynamic batch проверяется отдельно для batch=1 и batch>1.
- Экспорт через совместимый torch 2.2.2 exporter без dynamo параметра.
- onnx.checker structural check + ORT CPU InferenceSession + parity с sigmoid(final_state) на идентичных validation inputs.
- Допуск raw probability: abs(reference-exported)≤1e-5+1e-4×abs(reference) для каждого значения. Сохранить выборку/seed/версии, максимальную абсолютную ошибку и pass/fail. Разница решений на границе threshold при допустимой численной ошибке не скрывается: окончательные метрики считаются по ONNX.
- До проверки файл временный. После успешных проверок он атомарно публикуется и связывается с metrics через SHA-256.

## History/report contract

Update record отражает настоящий optimizer.step; validation record отражает конкретное измерение. Номер sampling iteration и optimizer update не взаимозаменяемы. Loss — weighted training BCE; не маркировать его как validation loss. Подробные поля — data-model.md.

Первый содержательный раздел report.html — final validation metrics с model hash, threshold, TP/FP/TN/FN, recall/precision/F1/accuracy и фоновым proxy с объяснением. Второй — фактические train loss/update и validation curves по стадиям, с раздельными единицами измерения. Третий — actual dataset sizes/shapes/sources/splits, generation/augmentation settings, review summary и доступные durations/provenance. Заголовок страницы и краткий run identity допускаются до первой секции, но не отдельная секция конфигурации перед метриками.

HTML/SVG самодостаточны. Пропуски измерений не интерполируются как реальные точки; единственная точка показывается маркером. Все динамические текстовые значения экранированы. Доступные сведения показываются из snapshot; неизвестное маркируется явно.

Report-only проверяет SHA модели, snapshot, metrics/history/scores и export-check, пересчитывает агрегаты без inference и отображает те же округлённые числа. При отсутствии модели или первичных результатов не создаёт достоверно выглядящий полный отчёт. Удалённый HTML при сохранённых валидных источниках восстанавливается; существующая модель и данные остаются неизменны.

## Completion contract

manifest.json публикуется последним: status=complete, run_id, fingerprint, mode, hashes config/snapshot/history/selection/final-state/ONNX/export-check/scores/metrics/HTML. Полный запуск full-run.json связывает generation и training statuses и пути. Наличие только features или model.onnx не означает full complete.


> Host migration 2026-11-08: this document records the prior remote-worker implementation. Current architecture and commands are described in host-migration-plan.md, host-validation.md and ../../README.md. Piper/WakewordData contracts below are historical and removed from runtime.

# Исследование и решения

## Источники
Зафиксированный upstream ревизии 1efbebc146959c84b6a955e148214a4f345005dc скачан в source.ipynb. Локальный learn_models/train_wakeword (1).ipynb изменён и не заменяет upstream. Изучены learn_models/generation/positives, CharaCaller, BrainBoxCasePipeline, voice_clone/distillation и существующие deciders.

## Организация
Decision: стандартные dataclass, __call__, Chara.call и CaseCollection; новый WakewordData для отсутствующих операций.
Rationale: ParlerTts/Vosk уже есть, готового обработчика признаков не найдено.
Alternatives considered: локальные ML операции отвергнуты; монолит скрыл бы восстановление TTS/Vosk.

## Позитивы
Decision: исходная схема ParlerTts с voice description/seed, коротким prefix/suffix, Vosk, Verifier и фильтром допустимого слова. Дополнительно min(conf) выбранных токенов >= настраиваемого порога default=0.7; отсутствующий/невалидный conf и пустой срез → review. Минимум для нескольких токенов — проектное правило.
Rationale: исходный Verifier confidence не проверяет, пустой срез может вызвать исключение; нужны локальные проверки без изменения общего voice_clone verifier.
Alternatives considered: Whisper, целые команды, TTS без обрамления исключены; среднее confidence скрывает плохой токен.

## Повторы
Decision: 3N отдельно по class/split; N — целевое число пригодных исходных WAV до аугментации, общее по вариантам фразы. Проектный default: два технических повтора временной ошибки, затем замена; общая постоянная ошибка останавливает этап. Чтение статуса/результата существующего задания и повтор Vosk/обработки пригодного аудио не расходуют бюджет синтеза. Каждый новый запуск TTS, включая технический повтор после ошибки, резервирует новую попытку из 3N.
Rationale: отсутствие слова/низкий confidence требуют нового аудио/seed; бюджет должен переживать resume.
Alternatives considered: лимит партий неточен; бесконечные повторы исключены.

## Кэш
Decision: canonical settings и артефакты проверять до кэшируемого вызова; сохранять task_id и резервирование попыток.
Rationale: CharaCaller не сравнивает аргументы; brainbox_pipeline разделяет сохраняемые отправку/сбор.
Alternatives considered: автоматическая инвалидация и автоматический выбор каталога отвергнуты пользователем.

## Соответствие notebook
| Блок | Перенос | Отличие |
|---|---|---|
| Установка/preflight | installer/lock | без Colab, /content, глобальных patches |
| Embedding/melspectrogram v0.5.1 | resource manifest/хеши | проверка читаемости |
| MIT RIR | davidscripka/MIT_environmental_impulse_responses, 16 kHz | fixed snapshot |
| ACAV | davidscripka/openwakeword_features; первые 10% train, следующие 1% validation с flatten | без удаления исходника |
| FMA small | URL notebook, первые 1500 MP3, mono 16 kHz | manifest порядка, проверка ffmpeg |
| Позитивы generate_clips | исходный learn_models TTS/Vosk/cut | согласованная замена Piper |
| Негативы | generate_adversarial_texts + custom_negative_phrases, Piper | отдельная операция |
| Resample | scipy.signal.resample_poly, 16 kHz | отдельный выход без удаления всех NPY |
| augment_clips | train.py --augment_clips в decider | изолированное окружение |
| Четыре NPY | (M,16,96), finite | manifest последним |
| Обучение/экспорт | исключены | граница этап 13 |

Upstream клонирует openwakeword с master и не фиксирует транзитивный commit. Решение: при реализации проверить конкретную ревизию и закрепить commit/lock до генерации, плавающий master запрещён. Piper pin исходника — родитель 1a8c49bd29b3a132721086ee88f2253f788594a8, разрешённый SHA сохранять. Это проверка поставки зависимости; архитектурных альтернатив не оставлено.

## Передача данных
Decision: файлы/архивы через BrainBox cache; ресурсы на worker через installer; только безопасные относительные пути архивов.
Rationale: общего диска может не быть; ресурсы многогигабайтные, NPY проверяется mmap/порциями.
Alternatives considered: пути другого хоста и большие массивы JSON непригодны.


Source SHA256: 434603fa67d1a340e392c04d1e5754e88bc20b703c8a587f5ea4ac6fb8cdf6ca

## Итог исследования при реализации, 2026-11-04

Зафиксированы openwakeword 368c03716d1e92591906a84949bc477f3a834455 и Piper sample generator c9d824c0e2cce8bdeb000c219dc9cbc84df086ea. Последний — разрешённый родитель исходного pin. Старый requirements.txt Piper не соответствует его актуальному pyproject.toml; проверены реальные импорты generate_samples и datasets.

Проверенное окружение: Python 3.11.11, torch/torchaudio 2.2.2+cpu, NumPy 1.26.4, ONNX Runtime 1.17.3, SpeechBrain 0.5.16, PyArrow 16.1.0. Уточнены backports-strenum 1.2.8 и setuptools 80.9.0. Базовые зависимости BrainBox включены в единый requirements.lock.txt (189 пакетов), чтобы отдельный KaiaFoundationDependencies не изменял requests/tqdm после установки lock. requirements.build.txt фиксирует заголовки/средства сборки. Фактические версии проверочного Linux-окружения сохраняются в worker-environment.json.

### Полное соответствие этапов 1–13

| Этап notebook | Реализация | Отличие и проверка |
|---|---|---|
| 1. apt/pip | Controller, requirements/build/lock | изолированное окружение; Linux imports и настоящий HTTP worker |
| 2. репозитории/модель | WakewordDataInstaller и ResourceInstaller | фиксированные SHA исходников; явная передача model в Piper |
| 3. runtime patches | совместимые закреплённые зависимости | A/D не нужны с torchaudio 2.2; B/E заменены прямым импортом и model argument; C — таймауты загрузок; F относится к исключённому обучению |
| 4. preflight | settings.validate, resources.read_voice_models, prepare_resources | ранняя проверка, версии и хеши вместо скрытого состояния notebook |
| 5. mel/embedding | две ONNX-модели v0.5.1 | TFLite-копии не нужны ONNX-конвейеру; реальные модели дали четыре массива (2,16,96) |
| 6. MIT RIR | dataset snapshot → mono 16 kHz WAV | snapshot разрешается до загрузки; хеши каждого артефакта и агрегат набора |
| 7. FMA/ACAV download | возобновляемая загрузка и checksum | Range=200 перезапускает запись; подтверждён тестом |
| 8. FMA conversion | первые 1500 MP3 → mono 16 kHz | стабильный порядок и check=True; незавершённая распаковка не считается полной |
| 9. ACAV subsets | первые 10% train, следующие 1% validation с flatten | mmap/порции; точность срезов проверена на малом NPY; исходник не удаляется |
| 10. config | GenerationSettings и JSON | только поля подготовки данных; настройки сравниваются до кэша |
| 11. generation | ParlerTts/Vosk/cut для позитивов; исходный Piper для негативов | согласованная замена позитивов; негативы генерируются партиями с исходным порядком пар speaker, а не новым процессом на каждый WAV |
| 12. resample | normalize_audio / resample_poly | отдельный артефакт, исходник сохраняется; реальная проверка stereo 8 kHz → mono 16 kHz |
| 13. augment/features | augment_clips + compute_features_from_generator | исходные вероятности; оценка длины по 50 выборкам positive_test; n_total как в upstream; без запуска Model/training |

Для augmentation_rounds сохранено поведение upstream: список исходников повторяется, но n_total ограничен исходным числом WAV. Не обещается M=N×rounds. При несовместимой форме результат не публикуется.

### Остальные интеграционные решения

- Сохранён поиск ближайшего среза по расстоянию Левенштейна <=3 и проверка допустимых поверхностных вариантов цели. Confidence >=0.7 — дополнительное настраиваемое условие.
- Описания голосов используют исходный VoiceDescriptionGenerator; seed и идентичность закреплены за попыткой для восстановления. Новая попытка получает отдельное описание/seed.
- Каждый новый TTS расходует 3N, включая технический повтор. Повтор запроса к существующему заданию и повторы обработки не расходуют его.
- Stable task ID сохраняется до отправки. Уникальность Job.id в BrainBox препятствует двойной постановке. Неизвестный сетевой статус останавливает синтез.
- До двух технических повторов Vosk/обработки. После общего отказа возможен ручной resume с сохранением успешных входов; история не обнуляет бюджет.
- Пустые части Vosk result теперь возвращают [] вместо KeyError в brainbox/deciders/voice_analysis/vosk/app/service.py. Изменение необходимо для ожидаемой отбраковки, а не ложной ошибки распознавания.
- Поддерживается английский язык; новые языки не добавлены, поскольку исходный generate_adversarial_texts работает с английским.
- Для resource_specs ожидаемый sha256 необязателен: при наличии проверяется, иначе фактический хеш замораживается при первой подготовке. HF main разрешается в конкретную ревизию до формирования cache identity. Подготовленные файлы разрешены только под /resources worker. Фактические хеши обязательны в выходном manifest.
- При поздней отбраковке нормализованного исходника исключается его lineage; пригодные нормализованные записи не обрабатываются повторно. Проверено полным прогоном с подменённым BrainBox.


> Host migration 2026-11-08: this document records the prior remote-worker implementation. Current architecture and commands are described in host-migration-plan.md, host-validation.md and ../../README.md. Piper/WakewordData contracts below are historical and removed from runtime.

# Задачи: подготовка данных wakeword в Chara

**Основа**: spec.md, plan.md, research.md, data-model.md, contracts/pipeline.md, quickstart.md.
**Пути**: ниже относительно корня kaia, если не указано иное. Документы feature находятся в chara/wakeword/specs/001-migrate-wakeword-pipeline/.
**Формат**: checkbox, последовательный T-ID, необязательный [P], обязательная метка истории в фазах US.
**Проверки**: отдельный TDD-процесс не вводится; приёмочные проверки встроены в задачи интеграции согласно сценариям spec.
**Окружение**: записи в brainbox находятся вне текущего writable root; при реализации использовать штатное расширение доступа, не обходить ограничения. Конституция — незаполненный шаблон.

## Фаза 1: подготовка

- [X] T001 Сопоставить блоки chara/wakeword/specs/001-migrate-wakeword-pipeline/source.ipynb с исходными learn_models/generation/positives и записать окончательную таблицу переносимых операций и отличий в chara/wakeword/specs/001-migrate-wakeword-pipeline/research.md; сохранить SHA256 источника и перечень runtime-зависимостей.
- [X] T002 Создать пакеты и точки импорта chara/wakeword/__init__.py, chara/wakeword/positives/__init__.py, chara/wakeword/negatives/__init__.py, chara/wakeword/scripts/__init__.py без тяжёлых ML-импортов в процессе Chara.
- [X] T003 Создать каркас нового decider по образцам Vosk/PiperTraining в brainbox/deciders/voice_analysis/wakeword_data/{api.py,controller.py,settings.py,run.py,app/__init__.py,app/interface.py,app/service.py,app/installer.py} и зарегистрировать экспорт в brainbox/deciders/__init__.py.

## Фаза 2: общие основания

Все пользовательские истории требуют завершения этой фазы.

- [X] T004 Реализовать GenerationSettings и чтение JSON в chara/wakeword/settings.py: поля из data-model.md; «Непустые варианты, безопасное имя, положительные counts/rounds/batch, конечный confidence в [0,1], поддерживаемый язык»; default min_vosk_confidence=0.7; разворачивать defaults до canonical JSON, учитывать версии моделей, исключать из семантического сравнения адрес сервера и журнальные параметры.
- [X] T005 [P] Определить AudioCase, ResourceSpec/ResourceManifest, GenerationProgress, ReviewRecord, FeatureArtifact/RunResult в chara/wakeword/dto.py со всеми полями data-model.md, состояниями и reason_code; сохранить ограничения «accepted ≤ N, reserved ≤ 3N», «shape=(M,16,96), числовой dtype, M>0, finite» и правило «Путь worker не является переносимым id».
- [X] T006 После T004–T005 реализовать контракты prepare_resources/generate_negative_texts/generate_negative_audio/normalize_audio/augment_and_extract в brainbox/deciders/voice_analysis/wakeword_data/api.py и app/interface.py; передавать cache names/resource id/revision и ошибки с sample_id/stage, не локальные пути другого хоста.
- [X] T007 Реализовать безопасный обмен архивами и manifest в chara/wakeword/processing.py и brainbox/deciders/voice_analysis/wakeword_data/app/service.py: только относительные пути без выхода за каталог, пакетная передача WAV/NPY через cache, без массивов JSON и полной загрузки набора в RAM.
- [X] T008 Подобрать и проверить совместимые версии openwakeword, Piper sample generator и ML-библиотек в brainbox/deciders/voice_analysis/wakeword_data/requirements.txt, requirements.lock.txt и app/installer.py; закрепить конкретные commits и разрешённый SHA исходного Piper pin, исключить плавающий master и глобальный torch.load patch; записать проверку импорта и зависимостей в chara/wakeword/specs/001-migrate-wakeword-pipeline/research.md.

Контрольная точка: настройки, DTO, файловые контракты и окружение worker готовы.

## Фаза 3: US1 — получить обучающие данные (P1, MVP)

**Цель**: генерация до заданного объёма и четыре проверенных набора.
**Независимая проверка**: с подготовленными ресурсами выполнить малый полный запуск с двумя вариантами цели; проверить все выходы, отсутствие утечек между частями и review, бюджет и совместимость с потребителем.

- [X] T009 [P] [US1] Реализовать перенос описаний голосов, вариантов, уникальных seed и построение cases в chara/wakeword/positives/case.py; закрепить class/split до аугментаций, «Потомки и замены сохраняют class/split», без runtime-импортов learn_models.
- [X] T010 [P] [US1] Реализовать проверку Vosk и вычисление границ в chara/wakeword/positives/verification.py по исходному Verifier: допустимое слово и min(conf) выбранных токенов >= порога; пустое распознавание/срез, отсутствующий, нечисловой, не finite или вне [0,1] conf и невалидные границы/длительность отклонять; границы по серединам между соседними словами.
- [X] T011 [P] [US1] Реализовать chara/wakeword/review.py: review/<sample_id>/audio.wav и record.json с исходным аудио, доступными Vosk/confidence/timestamps, seed и причиной; «без аудио сохраняется метадата»; не удалять отклонённые примеры и не включать их в accepted manifest.
- [X] T012 [US1] Собрать отдельные voiceover/recognition/cut через Chara.call и BrainBoxCasePipeline в chara/wakeword/positives/pipeline.py после T009–T011; ParlerTts с короткими prefix/suffix, Vosk через uploader/cache, общие ошибки останавливают этап, ошибки записи остаются в CaseCollection.
- [X] T013 [US1] Реализовать добор позитивов и резервирование попыток в chara/wakeword/positives/pipeline.py: 3N исходных попыток по class/split, N общий по вариантам, остановка на точном целевом объёме; последнюю партию ограничить остатком цели и бюджета; до двух технических повторов Vosk/обработки сохраняют sample_id/пригодное аудио без расхода бюджета синтеза; каждый новый TTS, включая повтор после ошибки, резервирует новую попытку из 3N; отсутствие слова/низкий conf создают замену с новым seed; недобор не complete.
- [X] T014 [P] [US1] Реализовать фонетически близкие и пользовательские негативы в chara/wakeword/negatives/pipeline.py и brainbox/deciders/voice_analysis/wakeword_data/app/negatives.py по upstream generate_adversarial_texts/Piper, с class/split и ограничением 3N; позитивный Vosk predicate не применять; подключить методы к app/service.py после завершения остальных параллельных работ в нём.
- [X] T015 [P] [US1] Реализовать нормализацию mono 16 kHz через scipy.signal.resample_poly в brainbox/deciders/voice_analysis/wakeword_data/app/normalization.py; проверять каждую запись, сохранять lineage, не изменять исходное аудио; подключить к app/service.py последовательно.
- [X] T016 [US1] Перенести upstream augment_clips и получение четырёх NPY в brainbox/deciders/voice_analysis/wakeword_data/app/features.py и подключить к app/service.py после T014–T015; сохранять параметры, число rounds и split, исключить запуск обучения/экспорта и удаление чужих файлов; M признаков не приравнивать к N исходных WAV.
- [X] T017 [US1] Реализовать полный потоковый/mmap валидатор и атомарную публикацию в chara/wakeword/validation.py: четыре ожидаемых имени, «shape=(M,16,96), числовой dtype, M>0, finite», читаемость каждой строки, SHA256/size/lineage; completed manifest записывать последним, review и train/test не пересекаются.
- [X] T018 [US1] Собрать WakewordPipeline.__call__ в chara/wakeword/pipeline.py: ресурсы → позитивы/негативы → нормализация → аугментация/признаки → проверка/публикация; использовать Chara.current.folder, стандартный logger и сериализуемый RunResult; недобор/сбой сохраняет диагностику и не публикует complete.
- [X] T019 [US1] Выполнить независимую проверку US1 с подменённым BrainBox через Python-вызов Chara.start(output) и Chara.call(WakewordPipeline(settings)) с явно переданным проверенным resource manifest, без зависимости от CLI/examples/installers US2; описать отдельный сценарий US1 в chara/wakeword/specs/001-migrate-wakeword-pipeline/quickstart.md; записать результаты в chara/wakeword/specs/001-migrate-wakeword-pipeline/validation.md: два варианта цели, 0.69/0.70/0.71, пустой/невалидный Vosk, отказы этапов, ровно 3N, четыре читаемых массива и отделённый review.

Контрольная точка: MVP US1 работает с заранее подготовленными ресурсами.

## Фаза 4: US2 — запустить в чистом каталоге (P1)

**Цель**: документированные подготовка и запуск без notebook и скрытого состояния.
**Независимая проверка**: новый каталог, только документированные зависимости/источники; полный малый запуск и намеренно недоступный ресурс с понятной ошибкой.

- [X] T020 [P] [US2] Реализовать подготовку моделей embedding/melspectrogram, MIT RIR, FMA и ACAV в brainbox/deciders/voice_analysis/wakeword_data/app/installer.py: fixed revision/hash, возобновляемая загрузка с проверкой HTTP Range, временные файлы, проверка чтения и ffmpeg, RIR/FMA 16 kHz, ACAV первые 10% train и следующие 1% validation с flatten; не удалять исходники неявно.
- [X] T021 [P] [US2] Реализовать preflight и сохранение resources.json в chara/wakeword/resources.py: проверить доступность BrainBox/deciders/версий/ресурсов, поддержать готовые проверяемые ресурсы, ошибки содержат этап, причину и действие; Avatar не требуется.
- [X] T022 [US2] После T020–T021 подключить prepare_resources к brainbox/deciders/voice_analysis/wakeword_data/app/service.py и chara/wakeword/pipeline.py; сохранять разрешённые модели/версии/хеши рядом с результатами без зависимости от скрытого HF cache.
- [X] T023 [US2] Добавить некэшируемую run(settings, output) в chara/wakeword/pipeline.py и публичный экспорт в chara/wakeword/__init__.py; до Chara.start/call валидировать settings/каталог и атомарно сохранять settings.json; полную проверку совместимости существующего каталога завершает US3.
- [X] T024 [P] [US2] Создать chara/wakeword/scripts/generate.py с обязательными --config/--output по contracts/pipeline.md, тонким вызовом run и кодом 0 только для complete; неверные настройки, недобор и сбой дают ненулевой код, этап/причину/путь диагностики.
- [X] T025 [P] [US2] Добавить chara/wakeword/examples/minimal.json и full.json: computer, короткие Hi / go., confidence=0.7, явные resource specs; minimal по 2 исходных записи на class/split и одна round, full n_samples=2000/n_samples_val=1000/rounds=1/augmentation_batch_size=16 с явным переводом в counts.
- [X] T026 [US2] Описать реальные команды установки/подготовки BrainBox decider, зависимости, источники, диск, примеры CLI, выходы и восстановление ошибок в chara/wakeword/README.md и уточнить chara/wakeword/specs/001-migrate-wakeword-pipeline/quickstart.md; исключить /content, Colab и интерактивную подготовку.
- [ ] T027 [US2] Выполнить запуск из нового каталога по README и сценарий недоступного/повреждённого ресурса, записать команды, версии и результаты в chara/wakeword/specs/001-migrate-wakeword-pipeline/validation.md; проверить отсутствие зависимости от состояния предыдущего запуска.

Контрольная точка: US1 и US2 доступны по документации из чистого каталога.

## Фаза 5: US3 — повторить запуск (P2)

**Цель**: восстановление без смешивания конфигураций, повторного синтеза готового аудио и сброса бюджета.
**Независимая проверка**: завершённый повтор, прерывание после отправки/voiceover и изменение настроек; устаревший результат ни разу не признаётся актуальным.

- [X] T028 [P] [US3] Реализовать сохранение GenerationProgress и попыток в chara/wakeword/progress.py: «Атомарное резервирование до отправки; accepted ≤ N, reserved ≤ 3N; resume восстанавливает счётчики»; генерировать и атомарно сохранять стабильный task_id вместе с seed/class/split до сетевой отправки; отличать pending от rejected, не расходовать бюджет повторно при чтении существующей попытки.
- [X] T029 [P] [US3] Реализовать в chara/wakeword/run_state.py сравнение canonical settings/schema/model versions и preflight сохранённых manifest/хешей до кэша: при изменении настроек или недоказуемой совместимости новый каталог, при повреждении результата явная ошибка без скрытого полного пересчёта.
- [X] T030 [US3] Подключить T028–T029 к chara/wakeword/pipeline.py и chara/wakeword/positives/pipeline.py: находить уже отправленные задания по стабильному id, переиспользовать готовое аудио и отдельные этапы, восстанавливать бюджет/accepted/review; перед повторной отправкой проверить BrainBox по предварительно сохранённому task_id: найденное задание ждать/читать, подтверждённо отсутствующее отправлять с тем же id; при недоступности проверки остановиться с диагностикой без нового TTS; проверить защиту BrainBox от повторной постановки одного task_id.
- [X] T031 [US3] Подключить восстановление негативов и обработки в chara/wakeword/negatives/pipeline.py и chara/wakeword/processing.py: сохранять class/split/lineage, повторять только неудавшийся этап с пригодными входами, при поздней отбраковке исключать исходник из accepted и все его производные из активного manifest по lineage_id, сохраняя их для диагностики; генерировать замену той же class/split в пределах оставшегося бюджета и пересобирать затронутую группу признаков до публикации complete; недобор запрещает complete.
- [X] T032 [US3] Добавить итоговый report.json и понятные журнальные итоги через стандартный logger в chara/wakeword/reporting.py и подключить к chara/wakeword/pipeline.py: accepted/review/attempts по группам, причины, недобор, пути и status; не заменять механизм логирования Chara.
- [X] T033 [US3] Проверить завершённый повтор, прерывания до/после отправки и после voiceover, неизменность бюджета и сохранность review, изменение confidence/цели и повреждение одного NPY; записать результаты в chara/wakeword/specs/001-migrate-wakeword-pipeline/validation.md с подтверждением SC-004.

Контрольная точка: все три истории выполняются и проверяются отдельно.

## Фаза 6: завершение и сквозные проверки

- [X] T034 Сверить реализацию со всеми FR-001–FR-017 и SC-001–SC-005, исходным notebook и соседними пайплайнами; обновить таблицу соответствия и объяснения отличий в chara/wakeword/specs/001-migrate-wakeword-pipeline/research.md, включая FR-009a и отсутствие обучения/экспорта/целых команд.
- [ ] T035 Выполнить минимальный и полный сценарии chara/wakeword/specs/001-migrate-wakeword-pipeline/quickstart.md, проверить чтение всех выходов и совместимость с исходным потребителем; записать масштаб, длительность, версии, фактические объёмы и ограничения в chara/wakeword/specs/001-migrate-wakeword-pipeline/validation.md, не объявлять пропущенный полный запуск успешным.
- [ ] T036 Проверить документацию с разработчиком, не участвовавшим в переносе: получение набора и локализация намеренной ошибки по chara/wakeword/README.md; зафиксировать фактический результат SC-005 в chara/wakeword/specs/001-migrate-wakeword-pipeline/validation.md и исправить обнаруженные пробелы документации.

## Зависимости и порядок

T019 проверяет US1 с подменённым BrainBox без будущего CLI; реальный запуск проверяется T027 после T020–T026. Подготовка T001–T003 → основания T004–T008 → US1 T009–T019 → US2 T020–T027 → US3 T028–T033 → завершение T034–T036.
US2 resource installer/preflight можно разрабатывать после оснований параллельно с US1, но интеграция и приёмка требуют US1. US3 зависит от рабочих этапов US1 и точки входа US2. Независимость проверок означает отдельные сценарии приёмки, а не отсутствие общих зависимостей.

Внутри фаз: модели и контракты → предметные операции → интеграция → приёмка. [P] допускается только после предшествующих общих оснований; изменения одного service.py/pipeline.py подключаются последовательно, даже если предметные модули разрабатываются параллельно.

## Примеры параллельного выполнения

- Основания: T004 settings.py одновременно с T005 dto.py; T006 после обоих.
- US1: T009 case.py + T010 verification.py + T011 review.py; затем T012. После оснований отдельно разрабатываются T014 negatives и T015 normalization; подключения service.py последовательны.
- US2: T020 installer + T021 resources; затем T022. После контракта run T024 CLI и T025 примеры могут выполняться независимо.
- US3: T028 progress + T029 run_state; затем T030.
Это возможности организации работ, а не разрешение автоматически запускать дополнительных агентов.

## Стратегия поставки

MVP: фазы 1–3, US1 с подготовленными ресурсами; пользователь получает четыре набора и review, соблюдается 3N.
Следующее приращение: US2 — самодостаточная подготовка и запуск по документации.
Затем US3 — безопасное восстановление и проверки до кэша.
Финальная готовность требует всех трёх историй и сквозных проверок; MVP не объявляется завершением всего feature.


## Host migration implementation (2026-11-08)

- [X] T037 Add host-v2 schema, resource path configuration and old-output rejection.
- [X] T038 Move resource preparation, negative text generation and explicit OOV checkpoint to Chara.
- [X] T039 Replace negative Piper synthesis with individual durable Parler tasks; preserve 3N/review/resume.
- [X] T040 Run normalization, augmentation and explicit-path ONNX embeddings on the Windows host.
- [X] T041 Update Make check/setup/run for host dependencies/resources and only Parler/Vosk APIs.
- [X] T042 Remove WakewordData code/registration and Piper assets from configuration; keep user Docker/data.
- [X] T043 Validate unit/integration contracts and native CPU processing; update README/quickstart.
- [X] T044 Finish real BrainBox integration on the small local fixture.
- [ ] T045 Execute minimal/full production corpora runs after providing disk space; assess negative quality on real audio.
- [ ] T046 Validate Python 3.11 and independent-developer instructions.

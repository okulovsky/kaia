> Host migration 2026-11-08: this document records the prior remote-worker implementation. Current architecture and commands are described in host-migration-plan.md, host-validation.md and ../../README.md. Piper/WakewordData contracts below are historical and removed from runtime.

> Superseded architecture: the approved 2026-11-08 migration is defined in [host-migration-plan.md](host-migration-plan.md). The text below records the previous implementation and must not guide new Piper/WakewordData work.

# План реализации: подготовка данных wakeword

**Ветка среды**: 001-migrate-wakeword-pipeline | **Дата**: 2026-11-04 | [Спецификация](spec.md)

## Summary
Chara управляет этапами, BrainBox выполняет тяжёлые операции. Позитивы переносим из исходного learn_models/generation/positives: ParlerTts с короткими prefix/suffix → Vosk → проверка → вырезание слова. Остальные преобразования сохраняют семантику notebook. Обучение и целые команды исключены.

## Technical Context
Python >=3.11,<3.13 согласно корневому pyproject.toml. Зависимости: Chara, BrainBox, ParlerTts, Vosk; NumPy/soundfile/scipy; openwakeword в отдельном окружении нового decider WakewordData.
Хранение: каталоги Chara, WAV, NPY, JSON manifests, review; без БД.
Проверки: unittest с подменённым BrainBox и отдельный реальный интеграционный запуск.
Платформа: Python Chara; Linux/Docker worker с подходящим моделям устройством. Тип проекта: библиотечный пайплайн и тонкий script.
Производительность: пакетная обработка, mmap; целевые секунды не заданы.
Ограничения: 16 kHz, четыре массива (M,16,96), confidence=0.7, бюджет 3N исходных попыток. Объёмы train/test настраиваются, ресурсы многогигабайтные.

## Constitution Check
До исследования и после проектирования: PASS. Конституция содержит шаблон, дополнительных правил не выводим. Решения пользователя соблюдены. Готового decider аугментации/признаков не найдено; новый обработчик обоснован.

## Project Structure
Документы: plan.md, research.md, data-model.md, contracts/pipeline.md, quickstart.md, source.ipynb. tasks.md содержит текущий список реализации и проверок.
Файлы chara/wakeword: settings.py, dto.py, pipeline.py, resources.py, positives/{pipeline.py,case.py,verification.py}, negatives/pipeline.py, processing.py, review.py, validation.py, scripts/generate.py, examples/{minimal.json,full.json}, tests.
Новый brainbox/deciders/voice_analysis/wakeword_data: api.py, controller.py, settings.py, run.py, requirements.txt, requirements.build.txt, requirements.lock.txt, app/{interface.py,service.py,installer.py}.
При реализации изменения BrainBox затронут соседний каталог вне текущего writable root. Изменения включают новый decider и обработку пустых результатов Vosk.

## Последовательность
1. Проверить совместимость конкретных версий ML-зависимостей, закрепить commit/lock и resource manifest до полноценной генерации.
2. Некэшируемая точка входа проверяет canonical settings и сохранённые артефакты до Chara.start/call. Несовпадение требует нового каталога. Каталог без доказуемо совместимых настроек отклоняется.
3. Installers BrainBox подготавливают ресурсы: временная загрузка, проверка размера/хеша/читаемости, атомарная публикация.
4. Перенести исходные позитивы без runtime-зависимости от learn_models. Сохранить CaseCollection и Chara.call voiceover/recognition/cut.
5. Добавить confidence, review и добор. Резервировать попытку до отправки; сохранять seed/task_id; последнюю партию ограничивать остатком цели и бюджета. Resume не обнуляет бюджет.
6. Негативы: generate_adversarial_texts, пользовательские фразы и исходный Piper sample generator через WakewordData. Позитивный predicate к негативам не применять.
7. Закрепить split до аугментаций; потомки и замены сохраняют class/split. Нормализация до 16 kHz, аугментация и признаки через BrainBox. Аугментация и признаки могут составлять одну задачу для сохранения upstream.
8. Проверить каждый выход, атомарно опубликовать четыре NPY, completed manifest последним.

## Сравнение с соседними пайплайнами
| Соглашение | Образец | Критерий |
|---|---|---|
| Организация | voice_clone/distillation/distillation.py | класс с __call__, предметные этапы |
| Настройки | voice_clone/distillation/settings.py | dataclass |
| Запуск | voice_clone/scripts/voice_clone.py | тонкий script, Chara.start/call |
| Результаты | common/architecture/chara.py | Chara.current.folder |
| Ошибки | common/pipelines/brainbox/brainbox_case_pipeline.py | CaseCollection, case.error |
| Повторы | common/pipelines/repetitions | ограниченный добор |
| Кэш и лог | common/architecture/chara_caller.py | стандартные файлы; проверка до кэша |
| Позитивы | learn_models/generation/positives | исходные TTS/Vosk/cut |

## Валидация
FR-001/002: таблица research; FR-003/006/007/010: настройки/installers/quickstart; FR-004/008: NPY валидатор; FR-005/009: сравнение и resume; FR-011: отсутствие обучения; FR-012/013: контракты; FR-014–017: бюджет/review/confidence.
Проверки: 0.69/0.70/0.71, пустой Vosk, отсутствующий conf, пустой срез, отказ TTS, временный Vosk, общий отказ модели, ровно 3N, прерывание после отправки, повтор, смена настроек, повреждённый NPY, непересечение train/test и review/dataset.

## Complexity Tracking
Нарушений нет. Отдельный оркестратор, БД и общая система инвалидации не вводятся.


Каждый новый запуск TTS, включая технический повтор после ошибки синтеза, расходует одну попытку из 3N. Чтение существующего задания и повторы Vosk/обработки пригодного аудио не расходуют бюджет синтеза.
Стабильный task_id атомарно сохраняется до сетевой отправки. При восстановлении сначала проверяется задание с этим id: существующее ожидается/читается, подтверждённо отсутствующее отправляется с тем же id. Если проверка недоступна, процесс останавливается с диагностикой без повторного синтеза. Перед реализацией проверяется защита BrainBox от повторной постановки одного task_id.
При поздней отбраковке исходник исключается из accepted, все его производные по lineage_id исключаются из активного manifest, но сохраняются для диагностики. Замена сохраняет class/split и расходует оставшийся бюджет; затронутая группа признаков пересобирается до публикации complete. Недобор запрещает complete.

Дополнительные модули реализации: io.py (атомарная метадата), worker.py и brainbox_execution.py (адаптеры BrainBoxCasePipeline), progress.py, run_state.py, reporting.py. Проверки и ограничения приведены в validation.md.

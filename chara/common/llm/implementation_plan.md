# LLM refactoring — implementation plan

Companion to `regression.md`, which holds the call-site audit and the rationale for every decision.
This file is the execution order. When a step is ambiguous, `regression.md` §4 is the authority.

Tests: `conda run -n kaia python -m unittest` — never pytest, never system python.

---

## Target shape

```
chara/common/llm/
    __init__.py
    llm_setup.py            LLMSetup(engine, model), .default(), .debug()
    llm_request.py          LLMRequest — frozen; .default(), .edit(), create_task, execute, …
    builder.py              ILLMBuilder, LLMRequestBuilder, NoOpBuilder
    llm_request_applicator.py
    steps/
        step.py, assign.py, case_typization.py, custom_parse.py, custom_prompt.py,
        derived_case.py, image.py, options.py, questionnaire.py, result_typization.py,
        system_prompt.py, template.py, template_entities.py
        questions/          Question, QuestionList, Json, BulletPointDivider
    engines/
        llm_engine.py       ILLMEngine + debug/with_debug
        brainbox_llm_engine.py, gemini_llm_engine.py, mock_llm_engine.py
        ollama_task_view.py shared task introspection
```

Flow: `LLMSetup.default()` → `LLMRequestBuilder` → `.to_request()` → `LLMRequest` → `create_task(case)`
→ engine (call mode) or `create_brainbox_pipeline()` (batch mode).

---

## Stage 0 — unblock the package

`regression.md` §5. The package does not import as written.

1. `__init__.py` — imports `.llm_engine`, which does not exist at that level; export `ILLMEngine`,
   `LLMSetup`, `LLMRequest`, the engines.
2. `llm_request_applicator.py:32` — `postprocess_output` must `return result`.
3. `steps/template_entities.py:9` — iterate `self.kwargs.items()`, not `template_entities.items()`;
   export the step from `steps/__init__.py`, which also imports `CaseTypization` twice.
4. `steps/template.py` — drop the unused `additional_objects` field and the unused `copy` import
   (`TemplateEntities` replaces it).

---

## Stage 1 — core types

**`ILLMBuilder`** — `append(step)` abstract; every builder method (`template`, `custom_prompt`,
`system_prompt`, `options`, `image`, `result_type`, `questionnaire`, `parse`, `assign`, `entities`,
`derived_case`, `case_type`) implemented in terms of it; `to_request()` abstract.

| | `append` | `to_request()` |
|---|---|---|
| `LLMRequestBuilder(setup, steps)` | new builder with the step | `LLMRequest(setup, steps)` |
| `NoOpBuilder(origin)` | `self` | `origin` |

**`LLMSetup(engine, model)`** — `.default() -> LLMRequestBuilder` (empty), `.debug(flag=True) -> LLMSetup`
with `engine.with_debug(flag)`.

**`LLMRequest`** — frozen, does **not** implement `ILLMBuilder`. `.default() -> NoOpBuilder(self)`,
`.edit() -> LLMRequestBuilder` seeded with its setup and steps. Keeps `create_task`, `build_prompt`,
`postprocess_output`, `start_execution`/`join_execution`/`execute`, `create_brainbox_pipeline`.

`LLMRequestBuilder.default()` also returns `NoOpBuilder`, so a caller-supplied builder is equally
protected.

New on `LLMRequest`:

* `build_prompt(case) -> str` — render only; needed by `test_writing_ai.py` and `test_prompt.py`.
* `create_brainbox_pipeline()` raises unless the engine is BrainBox-backed (§4.8.2).
* `create_task` validates that a prompt was produced, instead of failing with a bare `TypeError`.

---

## Stage 2 — steps

**Parser signature changes to `(case, output) -> Any`** (§4.3) across `CustomParse`,
`ResultTypization`, `Questionnaire`. A parser may perform side effects on the case and return `None`;
`Assign` addresses are applied to whatever it returns. Divider stays `(str) -> list`.

New:

* `CustomPrompt(Callable[[case], str])` → `arguments['prompt']`.
* `DerivedCase(Callable[[case], Any])` → overrides the `case` template entity.

Changed:

* `JinjaTemplate` — `setdefault` `template_entities['case']` so `DerivedCase` wins regardless of order.
* `TemplateEntities` — accept plain values and callables `case -> value`.
* `ResultTypization` — `Serializer.parse(t).to_json_schema()` into `options.format`; parser =
  `Json.parse_array` when the declared type is a list/tuple (port `Json.Assigner._is_array`) else
  `Json.parse_object`, then `Serializer.from_json`; contribute an `example` template entity via
  `json.dumps(..., indent=2)`.
* `Questionnaire(questions)` — accepts a `QuestionList`, a dataclass type, or an `AddressLike` resolved
  on the case. Contributes `questions` / description / example template entities; sets
  `options.format = questions.get_format()`; parser = `questions.parse`. Synthesises the whole prompt
  only when no prompt step is present.
* `Image` — raise unless the addressed value is a `Path`. No uploading: images work only against a
  local BrainBox sharing the filesystem (§4.6; the upload plan is a TODO in
  `brainbox/framework/app/api.py`).

Move into `steps/questions/`: `Question`, `QuestionList` (from `chara/common/tools/llm/question.py`),
`Json` (`json_parser.py`), `BulletPointDivider`. Behaviour unchanged — `QuestionList.parse` must keep
returning a plain dict when there is no dataclass, since `SceneRules.resolve_ending_questions` does
`all(answers.values())` on it.

---

## Stage 3 — engines

* `ollama_task_view.py` — one helper reading `task.decider`, `task.method`, `task.arguments`
  (prompt / system_prompt / options / image) and `task.optionals.parameter`; raises on an unexpected
  decider or method. Used by Gemini, Mock and debug printing.
* `ILLMEngine` — `debug` attribute (default `False`) and a concrete `with_debug(flag=True)` returning
  `copy.copy(self)` with the flag set, so the api client is shared rather than reconnected. Debug
  printing shows model, prompt and answer.
* `BrainBoxLLMEngine` — `start`/`join` over `Chara.Apis.brainbox_api`.
* `GeminiLLMEngine` — introspects the task; ports the existing `Ollama.Options` → OpenAI mapping from
  `_research/novels/llm/gemini_llm_engine.py` verbatim, including the documented drops; reads the
  `Path` out of `arguments['image']` and inlines it as base64.
* `MockLLMEngine(*replies)` — `start`/`join`, token = index.

`SubstitutingLLMEngine` is **not** ported (§4.9).

Unit tests for the whole package before touching any call site: builder/no-op semantics, `default()` on
setup vs request, `edit()`, step composition, `ResultTypization` on an object and on a list,
`Questionnaire` in all three resolution modes, `Image` rejecting non-`Path`.

---

## Stage 4 — migrate `chara`, self-contained sites

These build their own requests and never exercise `default()`/`edit()`.

* **#3/#4/#5 `images/common/scenario/pipeline_factory.py`** — `create_task_builder` becomes a request
  builder: `JinjaTemplate(name, self.script_folders)`, `Options(temperature=…)`, `ResultTypization(t)`
  where a type is given, `Assign('clothing'|'scene')`, or plain `Assign('face')` for the untyped one.
  Decide how the factory gets an `LLMSetup` — simplest is to keep the `llm_model` parameter and build
  `LLMSetup(BrainBoxLLMEngine(), model)` internally, so `run_activity_catalog.py` and the tests are
  unaffected.
  The `clothing.jinja` / `scene.jinja` templates hard-code their JSON example; once `ResultTypization`
  supplies `example`, they can use it instead.
* **#6 `images/pony/scenarios/pipeline_factory.py`** — parser `(case, output)` doing `Json.parse_object`,
  truncating each list to `case.settings.tags_per_scene_attribute`, returning `Scene(**js)`, plus
  `Assign('scene')`.
* **#1 `images/common/activity/activity_catalog_pipeline.py`** — `JinjaTemplate('activity.jinja', (folder,))`,
  `Options(settings.options)`, parser `(case, output)` that runs `BulletPointDivider()` and merges into
  `case.activities` with dedup, returning `None`.
* **#2 `images/common/drawing/image_generation_pipeline.py`** — `JinjaTemplate('review.jinja')`,
  `Image('image')`, `Questionnaire('review_questions')` reading the list off the case,
  `Assign('review_answers')`. `review.jinja` already reads `case.review_questions.…` and can stay as is.
* **#7/#8 `nlu/datasets/negatives/`** — `JinjaTemplate('negative_template.jinja')` plus
  `DerivedCase(lambda case: _NegativeJinjaModel(...))`, and `CustomParse(divider=BulletPointDivider())`
  with a parser that strips, assigned to `phrase`.
* **#9 `nlu/datasets/text_dataset/`** — plain `JinjaTemplate(path)`; it otherwise delegates to
  `Paraphrase.Pipeline`, so it follows Stage 5.

Tests touched: `tests/test_images/test_scenario_pipelines/*`. They mock at
`BrainBox.Api.serverless_test([OllamaMock()])` and keep working as long as `create_task` still produces
an `Ollama … .question(...)` task.

---

## Stage 5 — migrate `chara/paraphrasing`

This is where `LLMSetup`, `default()` and `edit()` are actually used.

* **#14 `paraphrase_pipeline.py`** — `ParaphrasePipelineSettings.paraphrase_task_builder` becomes
  `setup: LLMSetup` (plus optionally a caller-supplied `LLMRequest` for the paraphrase step). Sibling
  pipelines receive `settings.setup` instead of `PromptTaskBuilder(settings.paraphrase_task_builder.model)`.
* **#10 `grammar_correction`**, **#11 `options_expanding`**, **#13 `words_translation`**,
  **#15 `utterances/prompter.py`** — replace `set_prompt(default)` with

  ```python
  request = x.default().template(Path(__file__).parent/'prompt.jinja').to_request()
  request = request.edit().parse(self._merge).to_request()
  ```

  The second statement is what keeps the pipeline-private parser when the caller supplies a request.
* **#12 `template_paraphrasing/pipeline.py`** — use a plain `isinstance` check rather than `default()`:
  the caller owns the template, the pipeline owns the parsing. Per §4.5 the manual two-phase split
  collapses into a single `create_brainbox_pipeline()` with the divider and parser on the request —
  `Chara.call` already caches the raw answers in `items.tar`, so re-running the merge does not re-call
  the LLM.
* Tests: `tests/test_paraphrasing/**`. Note `test_options_expanding.py` and `test_word_translation.py`
  pass a prompt-only builder to override the default template; they become complete requests.

---

## Stage 6 — migrate `_research/novels`

* **#16 `scenario/elaboration/elaborator.py`** — `ResultTypization(SceneHint)` replaces the hand-built
  schema and the `json.loads` + `serializer.from_json` pair; `Json.parse_object` is the fence-tolerant
  upgrade.
* **#17 `llm_character_chooser.py`** — parser `(case, output)` that strips, validates against the names
  derived from the case, and falls back to `RandomCharacterChooser`.
* **#18 `llm_continuer.py`** — parser `(case, output)` with the numbered-list regex, `random.choice`,
  the speaker-prefix strip, and `Message(..., case.character.name, False)`.
* **#19 `llm_question_answerer.py`** — `Questionnaire` resolved from the case; the `QuestionList` arrives
  per call from `ISceneRules.get_ending_questions`, so build the request per call or address it off a
  case field.
* **#20/#21** — plain requests with a `.strip()` parser.
* **#22 `private/`** — drop `SubstitutingLLMEngine` (and `Character.neutral_name` if it becomes dead);
  one engine, with `setup.debug()` on the writing setup instead of a second engine.

---

## Stage 7 — migrate `_research/creative_articulator`

* **#23 `ai/background/block_summarization.py`** — `TemplateEntities(summary_length=…)` replaces
  `additional_objects`. `prepare()` holds the `BrainBox.Task` from `create_task(node)` in
  `SummarizationBase.Task` instead of a prompt string; `execute()` runs it through the engine. Note
  `SummarizationBase.__init_` is a typo for `__init__` and never runs.
* **#24 `ai/writing/writing_ai.py` + `app/service.py`** — same: build the task under `lock(root)`,
  execute after release. `build_prompt` stays for the tests.

---

## Stage 8 — delete and verify

1. Delete `chara/common/tools/llm/` and `_research/novels/llm/`.
2. `grep -rn "tools.llm\|novels.llm\|PromptTaskBuilder\|JinjaPrompter"` over `chara` and `_research` —
   expect zero hits. `chara/nlu/pilot_research/better_nlu/*` imports
   `chara.paraphrasing.common.llm_tools`, which already does not exist; delete or fix.
3. Full test run.

---

## Invariants worth a test each

* `postprocess_output` returns the parsed result (Stage 0 bug 2 regressing is silent).
* A divider outside a pipeline raises — the guard in `LLMRequest.postprocess_output` already does this,
  and it is why `execute() -> TResult` is accurate.
* Two same-priority parsers raise "Parser is ambiguous"; `Assign` may appear more than once.
* `Options` merge is last-wins per field, and `None` never clobbers a set value — #3/#5 pass
  `Ollama.Options(temperature=None)` unconditionally and rely on this.
* `JinjaTemplate` does not overwrite a `case` entity set by `DerivedCase`.
* `Image` raises on anything that is not a `Path`.
* `create_brainbox_pipeline` raises for a non-BrainBox engine.

## Known regression

Application failures now produce the generic `"Application error: …"` from
`BrainBoxCaseResultApplicator` rather than the hand-written per-case messages in #10, #11 and #12.

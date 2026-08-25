# drama

`drama` is the interactive-fiction half of `creative_articulator`: it plays a story with a human in the
loop. The human is one of the characters (the protagonist), the LLM plays everybody else, and the story
advances scene by scene until it is finished.

The package is organized as four layers, each one built strictly on top of the previous ones:

| layer      | question it answers                                         | knows about LLMs? |
|------------|-------------------------------------------------------------|-------------------|
| `data`     | what is a story made of?                                     | no                |
| `driver`   | how does a story advance, and how is that exposed to a chat? | no                |
| `scene`    | what happens inside one scene?                               | yes               |
| `scenario` | where do the instructions for a scene come from?             | yes               |

Dependencies only ever point upwards in that table: `driver` imports `data`, `scene` imports `driver` and
`data`, `scenario` imports all three. Nothing imports downwards.

Everything rests on `creative_articulator.common.Node` (one level up, shared with `epic`), and the
`demo/` folder wires the whole stack into a runnable application.

---

## The substrate: `Node`

`Node` is a tree node that is also a type-keyed dictionary:

```python
node[ISceneRules] = SceneRules(...)     # the key is the type itself
rules = node[ISceneRules]               # missing keys are default-constructed by ensure()
node.attach(SceneEngine(...), custom_type=IEngine)   # store under an interface, not the concrete type
```

Two consequences shape all the code below:

* **A node has no schema.** Each layer attaches its own types to the same nodes: `driver` attaches
  `SceneState`, `scene` attaches `ISceneRules`, and neither has to know about the other.
* **Storing under an interface is how polymorphism is injected.** `node[IEngine]` returns whatever engine
  was attached to that node, so the driver can run a tree in which every node behaves differently.

Nodes also carry navigation helpers used throughout: `parent`, `children`, `root`, `ancestors()`,
`siblings()`, `descendants()`, and the `left_excerpt()` / `right_excerpt()` pair used to linearize the
context around a node.

---

## `data` — the vocabulary

No behaviour, only the things a story is made of.

**`Message`** — one utterance. Its `content` is a `MessageContent`: a list of `MessageSegment`s, each
either speech or an action, which is how `Sharik: I found it *shakes the snow off*` round-trips between
text and structure. `speaker is None` means narration. `from_user` marks the human's own messages, and
`id` is a uuid used later to address the message from the chat UI.

**`IDiff`** — a change to the story, with a single method `apply(root)`. **Diffs are the only way story
state ever changes.** That is the central design decision of the whole package: because every change is a
reified object, a story can be replayed from a list of diffs, which is what saving, loading, branching
and rewinding are all built on. `DiffList` is just `list[IDiff]`, used as a node key.

**`CharacterReference`** — a reference to one or several `chara` `Character`s, with the grammar attached.
It composes with `+` and `-`, and exposes `name` ("Matroskin and Sharik"), `pronoun`, `is_()` / `has_()`
so that prompt templates can talk about a group without special-casing the count.

**`Character`** — re-exported from `chara`; `drama` does not define its own.

---

## `driver` — managing the interface

The driver binds together the story progress and the UI. 
It knows nothing about scenes, prompts or LLMs. It sees a tree of nodes in
which every node has an `IEngine`, and it does not care what those engines do.

### State

* **`StoryState`** lives on the root: `current_node` (where the story is right now) and `finalized`.
* **`SceneState`** lives on every node: `messages`, `finalized`, plus `summary` / `shortening` /
  `shortening_index` which the scene layer fills in.

### Engines

```python
class IEngine(ABC):
    def generate(self, current: Node) -> Iterable[Listen | Message | IDiff]: ...
```

An engine is a generator. Yielding a `Message` means "this was said", yielding an `IDiff` means "this
changed", and yielding **`Listen`** means "stop, it is the human's turn". `Listen` is a sentinel, not a
diff — it never touches the story.

* **`SequenceEngine`** is the usual root engine: it walks into the first non-finalized child, and pops
  when all children are done. A story is thus a flat sequence of scenes by default, but nothing stops a
  root engine from choosing children in any other order.
* **`MockEngine`** produces scripted output (`MANY(5)`, `POP`) and exists for the tests.

### `StoryDriver`

`StoryDriver` owns the story tree and drives the loop:

```python
driver = StoryDriver(story)     # deep-copies the tree as an immutable backup
driver.reset(diffs)             # restore the backup, then replay the diffs to reach a known state
for diff in driver.generate():  # ask the current node's engine for the next diffs
    ...
```

`generate()` repeatedly asks `current[IEngine]` for output. `Message`s are automatically wrapped into
`AddMessageDiff`. An **`IFlowBreakingDiff`** (`PushDiff`, `PopDiff`) ends the current engine's turn,
because after a push or a pop `current_node` has moved and the old engine is no longer the one in charge.
`Listen` ends generation entirely and hands control back to the human.

The basic diffs are `AddMessageDiff` (append to the current node's `SceneState`), `PushDiff` (descend
into the first non-finalized child) and `PopDiff` (finalize the current node and go back up; popping past
the root finalizes the story).

### `chat_service` — the story as a chat

`ChatService` binds the driver to the `avatar` daemon: it handles `InitializationEvent`, `TextEvent`,
`SwipeChatMessageEvent` and `DeleteChatMessageEvent`, and emits `ChatCommand`s that the web frontend
renders, followed by a `ChatConfirmation`.

The important thing to understand here is that **there are two trees**:

* the **story tree** — scenes, engines, `SceneState`; owned by `StoryDriver`, rebuilt from scratch on
  every `reset()`;
* the **chat tree** — owned by `NodeHelper`, one node per message, holding that `Message`, the
  `DiffList` produced while it was current, and a `TreeStatus` marking the selected branch. This is the
  tree that gets pickled to the save file.

The chat tree is the history, and the story tree is derived from it: to move anywhere in the history,
`ChatService` collects the `DiffList`s along a branch and calls `driver.reset(diffs)`. Alternative
continuations are siblings in the chat tree, which is exactly what swiping between variants does, and
deleting a message removes a whole level of siblings and re-generates.

Generation is interruptible: each handler records its own event id under a lock, and the generation loop
abandons its work as soon as a newer event takes over.

---

## `scene` — what happens inside one scene

`SceneEngine` is an `IEngine`, so from the driver's point of view a scene is just another node. Inside,
it is a fixed pipeline of injected collaborators.

### Data attached to a scene node

* **`ISceneRules`** (per scene node) — everything specific to this scene. Its `actors` field is an
  `Actors`: `protagonist`, `characters`, the `opening` line, `length_factor`, plus `get_sides(lead)` /
  `others(lead)` / `all()` used when building prompts. The rest of the interface is described below.
* **`SceneSettings`** (on the root, shared by all scenes) — the numeric knobs: desired number of user
  messages, message length in words, summary length, shortening thresholds, and the story `intro`.

### `SceneEngine.generate`

1. On first entry: run the `IElaborator` (if any), then emit the opening line.
2. Emit the announcements the rules have for the current stage.
3. Loop: ask `ICharacterChooser` who speaks next; while it returns a character, ask `IContinuer` for that
   character's line. Returning `None` ends the round.
4. Decide whether the scene is over: `ISceneRules.is_custom_scene_ending()`, or otherwise ask the
   `IQuestionAnswerer` the rules' ending questions and let the rules interpret the answers.
5. Not over → run the `regular_postprocessor`, then `Listen` (the human's turn).
   Over → run the `final_postprocessor`, then `PopDiff`.

`SceneEngine.scene_engine_debug_run` runs the same loop with the protagonist played by the LLM too, which
is how `demo/debug.py` produces a whole script without a human.

### The interfaces

| interface            | responsibility                                                    |
|----------------------|-------------------------------------------------------------------|
| `ICharacterChooser`  | who speaks next, or `None` to end the round                        |
| `IContinuer`         | produce one `Message` for a `ContinuationCase` (scene + character + hints) |
| `IQuestionAnswerer`  | answer a `QuestionList` about the scene                            |
| `IScenePostprocessor`| yield diffs after a round or at the end of the scene               |
| `IElaborator`        | yield diffs when a scene is entered for the first time             |

### `ISceneRules` — the authored content

The rules are what makes one scene different from another. `SceneRules` is the standard implementation:
it takes the `Actors` of the scene, plus a `SceneHint` and the ending questions. A `SceneHint` holds a
list of `SceneStageHint`s, each with per-character hints, an optional announcement, and a `progress`
value in `[0, 1]`. Progress is measured as the number of protagonist messages so far
against `desired_user_messages_count_in_scene`, so the scene drifts through its stages as it goes on:
early stages tell the characters to hold back, later ones to come out with it. Announcements fire once,
when their stage is first reached. Ending questions are asked of the `IQuestionAnswerer`, and by default
the scene ends when all of them are answered yes.

Hints are *guidance*, not commands — they are placed in the prompt, and whether a character follows them
is up to the model.

### `implementations`

The concrete, LLM-backed pieces, each paired with a `.jinja` template sitting next to it:

* `RandomCharacterChooser` — picks whoever has spoken least; no LLM, and the fallback for the next one.
* `LLMCharacterChooser` — asks the model who should answer.
* `LLMContinuer` — generates a line for a character, parsing a numbered list of candidates and picking one.
* `LLMQuestionAnswerer` — a questionnaire request whose questions come from the case.
* `Summarizer` — final postprocessor, yields `SceneSummaryDiff` (a scene's summary is what later scenes see).
* `SceneShorteningPostprocessor` — regular postprocessor; once a scene grows past
  `min_messages_for_shortening`, condenses the older messages into `shortening` and records how many were
  folded in, so prompts stay bounded.

Note that the postprocessors express their results as diffs (`SceneSummaryDiff`, `SceneShorteningDiff`)
rather than mutating `SceneState`, so summaries and shortenings survive save/load and branch switching
like everything else.

---

## `scenario` — where the rules come from

The top layer removes the last piece of hand-written content: instead of authoring `SceneStageHint`s by
hand (as `demo/scenes.py` does), it derives them.

* **`Plan`** — a prose statement of what the scene is about, plus the `SceneHint` that implements it.
* **`IPlanFactory`** — `describe(setup) -> Plan`. It receives the setup, so a plan is written against
  whoever happens to be in the scene rather than against fixed names.
* **`Persuasion`** — the first concrete factory: "these characters must convince *target* to agree to
  *goal*", expanded procedurally into three stages (refuses → wavers → gives in) with matching hints for
  the lead and for everyone else.
* **`Elaborator`** — an `IElaborator` that takes an `ElaborationCase` (the node, the plan, and a JSON
  example of the expected shape) and asks the LLM for a richer `SceneHint` than the factory's mechanical
  one.

This layer is the least finished part of the package: `Elaborator.create_hint` works, but
`Elaborator.elaborate` — the hook `SceneEngine` actually calls on first entry — still raises
`NotImplementedError`.

---

## `demo` — the stack, assembled

`demo/` is a full example built on the Prostokvashino characters, and the best place to read the wiring:

* `characters.py` — three `chara` `Character`s.
* `scenes.py` — two hand-authored scenes: openings, staged hints, announcements, ending questions.
* `story.py` — `build_story()`: a root node with `SceneSettings` and a `SequenceEngine`, and one child
  per scene carrying `ISceneRules` (which holds the scene's `Actors`) and a fully-assembled `SceneEngine`.
* `demo.py` — the interactive application: starts an `AvatarServer`, binds `ChatService` to the daemon,
  opens the browser. `--reset` discards the save file, `--debug-llm` prints prompts and answers.
* `debug.py` — headless: runs every scene with the LLM playing all sides and prints the resulting script.

Both entry points take the character the protagonist plays as an argument.

---

## Tests

`tests/test_drama` mirrors the layers: `test_driver/test_story_driver` covers the engine loop and scene
switching with `MockEngine`, `test_driver/test_chat_service` covers branching, deletion and interruption,
and `test_scene/test_integration` covers the scene pipeline.

```
conda run -n kaia python -m unittest discover -s creative_articulator/tests/test_drama -t .
```

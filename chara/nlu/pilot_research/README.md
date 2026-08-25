# pilot_research

Finished pilot studies, kept in the shape they were run in.

**Nothing here is expected to import, run or be tested.** These scripts reference
modules that have since been renamed, moved or deleted — `chara.paraphrasing.common.llm_tools`,
`chara.paraphrasing.negatives`, `chara.paraphrasing.intents`, `chara.nlu.dataset`,
`talents.better_nlu.model`, and so on. That is intentional: the value of the directory is the
record of what was actually done, not a working artefact.

So:

* do not "fix" the imports here as part of a refactoring, and do not delete a file because a
  grep for an old symbol hits it;
* do not add these paths to test discovery;
* if you are checking that some old API is gone from the codebase, exclude this directory
  from the grep.

If a pilot ever needs to be revived, port it into a live package rather than repairing it here.

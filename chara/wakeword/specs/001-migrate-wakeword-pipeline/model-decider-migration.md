> Decision update (2026-11-08): the user selected ParlerTts for negative synthesis, no Piper blending, and host-side execution of WakewordData responsibilities. Earlier pending choices and recommendations below are historical. See host-migration-plan.md.

# Proposed separation of model-backed generation (not yet approved)

Status: investigation; no implementation or specification change. 2026-11-08.

## Evidence

- Piper app/interface.py exposes one-WAV voiceover with speaker, noise_scale, length_scale, noise_w, but no seed, blending or batch API.
- Piper app/service.py starts a Piper CLI subprocess for each invocation, using /resources/models/<model>.onnx.
- Piper settings.py currently pairs the English alba ONNX with an alan JSON; validate and repair this pair before using it.
- The pinned piper-sample-generator generate_samples.py iterates speaker pairs and applies SLERP to their embeddings. Default blend weight is 0.5. This is a material difference from selecting a speaker ID.
- It chooses synthesis settings once per internal batch, cycles texts, and advances through speaker pairs. Changing batching changes the generated sample schedule, not just throughput.
- WakewordData service fixes batch_size=min(count,7), noise scales 0.98, lengths 0.75/1/1.25, seeds Python/NumPy/PyTorch, and uses the pinned .pt model.
- Chara generation/negatives/pipeline.py persists group attempts and a shared task/seed for each batch. generation/brainbox_execution.py queries saved job IDs before dispatch and refuses synthesis if task status cannot be established.
- WakewordData also computes ONNX mel/embedding features through compute_features_from_generator; this is model inference, separate from audio synthesis.

## Proposed contract for a Piper batch method

Keep voiceover unchanged. Add a separate method for the pinned sample-generator backend, with a separately installed .pt checkpoint and config. Do not pass WakewordData resource paths across containers: install assets in Piper resources and refer to them by model ID.

Inputs: texts, ordered sample IDs, seed, model ID, internal batch size, lengths/noise settings, blend weights. Chara owns class/split, budget, task identity and replacements. Reject duplicate IDs, invalid counts/settings and unavailable models before synthesis.

Output: archive of WAVs and manifest mapping sample IDs to relative paths, requested schedule, model identity and backend revision. Validate count and audio readability before accepting results. Do not claim successful partial output unless per-sample failures are explicitly represented. For a first fidelity-preserving migration, retain current whole-batch failure semantics rather than silently synthesizing a different schedule.

A successful lost HTTP response must be recovered by the same BrainBox job ID. A confirmed failed job may require a new attempt under the existing 3N rules. Never hide additional synthesis retries inside the decider. Existing BrainBox queue/cache APIs support this; no framework changes are required.

Seed controls stochastic synthesis but does not promise byte-identical output across different library versions/hardware. Freeze model hashes, generator commit, dependencies and batch schedule. Treat migration as an incompatible generation configuration and require a new output directory.

## Verification before accepting migration

1. Same fixed inputs, model, seed, dependency environment and batch size: compare old/new text and speaker-pair schedule, blend settings, sample count, ordering, sample rates and durations; compare audio where deterministic execution permits.
2. Cover nonmultiple batch counts, one sample, multiple texts and replacement batches; check that batching does not reset speaker progression unintentionally.
3. Interrupt after dispatch/after completion and resume: no duplicate TTS; unknown job state stops; budget and class/split remain intact.
4. Missing model, OOM and malformed/partial archives cannot publish complete datasets; originals and review survive.
5. Measure wall time and peak RAM for one-WAV tasks versus batching; no performance claim before measurement.
6. Check setup installs the correct backend/model only as needed, using server resource paths. Existing normal Piper voiceover continues working.
7. Re-run four-output dataset shape/lineage checks. Assess negative diversity and false activations separately; shapes alone cannot prove equivalent training quality.

## Decisions needed

- Preserve original .pt generator and blended voices in a new Piper batch method (recommended), or accept ONNX-only behavior with a new quality baseline?
- Scope: move audio synthesis only, or also separate ONNX feature inference from WakewordData? This document does not narrow the requested goal; both remain open until agreed.
## Additional evidence: ONNX alternative

The pinned generator also exposes generate_samples_onnx. Its schedule cycles models and synthesis parameters, then enumerates individual speaker IDs; it does not interpolate speaker embeddings. Thus ONNX dataset generation is technically supported upstream, but is not equivalent to the .pt branch currently called by WakewordData. Existing Piper can expose similar individual-speaker settings through ordinary tasks without adopting the .pt backend. A batch API would still avoid a separate CLI process per sample.

Current positive synthesis already uses ParlerTts.voiceover_with_description(model=mini-v1, seed=case.seed), and recognition uses Vosk.transcribe_to_array. These paths need no backend migration. Negative text generation uses openwakeword.generate_adversarial_texts; do not assume it is an LLM merely because it generates text. Its dependency/algorithm boundary should be documented before moving it to a model decider.

No backend or feature-inference boundary has been selected by the user yet. Pending explicit choices must not be represented as accepted requirements.
## Conditional model inference in negative text generation

Inspection of the pinned upstream generate_adversarial_texts in .staging/data.py (around line 896) reveals a conditional DeepPhonemizer fallback: dictionary words use pronouncing/CMUdict lookup and combinatorial sampling, but unknown words trigger download of en_us_cmudict_forward.pt into the installed openwakeword package and run dp.phonemizer.Phonemizer.from_checkpoint. Therefore moving only Piper synthesis does not remove all generative model inference from WakewordData for arbitrary target variants.

For a strict model separation, extract phoneme prediction behind a profile decider with explicit checkpoint installation/version/hash and no first-request implicit downloads. Preserve CMUdict phones and stress conventions; replacing the fallback with another phonemizer requires normalization and behavior checks. Do not silently disable unknown words or change their pronunciation. The default computer example alone will not exercise this branch. Add an out-of-dictionary target test and assert that WakewordData no longer downloads or loads a checkpoint. This is additional evidence for the pending boundary decision, not an approved implementation change.
## Final inventory and proposed acceptance boundary

| Operation | Current owner | Proposed profile owner | Compatibility gate |
|---|---|---|---|
| Positive TTS | ParlerTts | ParlerTts (unchanged) | short context, model mini-v1, seed |
| Word recognition | Vosk | Vosk (unchanged) | confidence/crop behavior unchanged |
| Negative TTS | WakewordData | Piper batch backend, pending approval | .pt model, blended voices, schedule |
| OOV phoneme prediction | implicit DeepPhonemizer in WakewordData | explicit phoneme-model decider, pending scope agreement | CMUdict-compatible output, pinned checkpoint |
| Mel/embedding inference | WakewordData | profile feature decider if strict boundary selected | same ONNX hashes, (M,16,96), same recipe |
| Dictionary sampling, crop, normalization, augmentation | existing orchestration/processing | keep non-model responsibilities separate | no changes to split, review, 3N or recipe |

Existing EspeakPhonemizer delegates to espeak-phonemizer and returns nested token sequences. Its API has no DeepPhonemizer checkpoint/model selection or CMUdict-output guarantee. It is not a drop-in implementation of the current OOV fallback. A conversion and pronunciation regression corpus would be necessary; equal interface purpose is not evidence of equal outputs.

Recommended full-fidelity route: preserve .pt synthesis in a new Piper batch method; explicitly expose the current phoneme checkpoint via a profile decider; separate embeddings only if the agreed boundary covers all inference. Keep fundamental BrainBox framework APIs unchanged. Update check/setup requirements to match the selected deciders/models and make assets owned by their executing decider, rather than sharing container-local paths.

Research evidence, proposed contracts and regression gates are documented. Agreement is not complete: the pending user choices for the synthesis backend and inference boundary remain necessary before implementation. No runtime changes are authorized by this research continuation alone.

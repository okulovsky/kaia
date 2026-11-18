# Implementation evidence — 2026-11-17

## Status

Implementation and local native/contract checks are complete. Full acceptance is **not complete**: Docker Desktop Linux engine is unavailable; real generation, Linux image/self-test, remote HTTP/no-shared-filesystem smoke and full remote curriculum have not run. Tasks T018/T036/T037/T046/T050/T054 remain open. No unavailable check is counted as passed.

No generic BrainBox/Chara transport/controller helpers were changed. The only existing BrainBox registration change exports WakewordTraining. Makefile was removed; canonical generation/numeric code moved to brainbox/pipelines/wakeword, with deprecated typed module aliases for compatibility.

## Executed checks

- Windows Python **3.12.16**: full unittest discovery **97 tests, 62.827s, OK**, no skips; then the two newly added FileLike/reflection transport tests **2 tests, 0.388s, OK**. **99 distinct passing tests** across those invocations.
- Windows Python **3.11.16**: native/contract/import/recovery subset **23 tests, 30.657s, OK**, no skips; additional transport contracts **2 tests, 0.520s, OK**. **25 distinct passing tests**.
- Ruff **0.17.4**, run from kaia root over canonical pipelines, new decider, old wrappers and all wakeword tests: **All checks passed**.
- mypy **2.4.1**, same scope, `--follow-imports=silent --ignore-missing-imports --explicit-package-bases`: **Success, 185 source files**. Existing unrelated project modules are not claimed to have strict type coverage.
- `git diff --check`: passed. Generated app/wakeword_core and resource-profile.json are ignored build staging; no generated model/cache/resource files were staged.
- Builder staging executed locally. Python 3.11 imported staged wakeword_core.execution and service with Chara imports prohibited: **passed**. This is a Windows import check, **not Linux image validation**.
- Runtime numeric versions: NumPy1.26.4, Torch2.2.2+cpu, ONNX1.16.1, ORT1.17.3, Matplotlib3.9.2. Dedicated runtime lock pins 26 CPU packages. Linux wheel compatibility still requires T036; CUDA dependencies are excluded because the target artifact is the +cpu wheel.

Reproduction from kaia root:

```powershell
python -m unittest discover -s chara/wakeword/tests
python -m ruff check brainbox/pipelines/wakeword brainbox/deciders/voice_analysis/wakeword_training chara/wakeword
python -m mypy --follow-imports=silent --ignore-missing-imports --explicit-package-bases brainbox/pipelines/wakeword brainbox/deciders/voice_analysis/wakeword_training chara/wakeword/__init__.py chara/wakeword/generation chara/wakeword/training chara/wakeword/scripts chara/wakeword/tests
```

Use a Python environment with the listed dependencies; invocation of `python` alone does not select Conda automatically. The explicit unittest command now discovers the two additional transport tests as well.

## Native artifacts and actual measurements

Persistent, synthetic-only evidence: `temp/wakeword/feature003-native-002/validation.json`, `performance.json`, `host/wakeword.onnx`, `host/report.html`, `host/report_ru.html`. Training fixture has three rows per class/split, separately generated numeric ACAV-shaped background. These numbers do **not** measure real wakeword quality.

The control run performed **3 real optimizer updates**, across three stages, in 3.797s. Dataset ZIP: 65371 bytes; result ZIP: 738251 bytes. Final ORT supervised TP=3, FP=0, TN=3, FN=0; recall/precision/F1/accuracy=1.0 on this deliberately separable synthetic fixture. Background: 0 positive windows / 10 windows, 40 feature frames at .08s; waveform_hours=null.

ONNX SHA256: `9bdaf667411b179b6fc42185f29f259db83ac122a21b241e826d3cc116dbf5bd`. Corpus identity: `428f35bdcfc12bf34681912ba09d0542bdbecf080ff627131ef05eaab2eccb27`. Full request/execution/archive/manifest hashes are in validation.json, not invented from a report.

The result ZIP was streamed to a separate local host directory and verified against reference/hash/allowlist. Host export contains no PT/background/input dataset. Both HTML files were deleted and rebuilt. Model/history/all saved-score/immutable-manifest hashes stayed unchanged. A separate process rebuilt reports with Torch/ORT/ONNX/openwakeword imports blocked and BrainBox.Api.execute forbidden: **passed**. Local-render.json records new HTML hashes without invalidating the immutable server archive/reference.

Two distinct synthetic corpora subsequently trained against the **same** server background. urllib downloads were prohibited, shared background file hashes remained unchanged. 2GiB archive limits and unsafe member/header/finite checks are exercised in contract tests. Measured process RSS includes imported Torch/ORT/renderer and is sampled every20ms; same process executes server and host phases, so these are scoped local-phase measurements, not separate-machine memory claims:

| Run | Dataset bytes | Result bytes | Server seconds | Server peak process RSS bytes | Host receive/verify seconds | Host peak process RSS bytes |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 65371 | 738278 | 4.307 | 345219072 | 0.076 | 346001408 |
| 1 | 65354 | 738267 | 0.822 | 350015488 | 0.066 | 350380032 |

No production-scale RSS/SLA or actual HTTP network throughput is inferred from these small measurements.

## Real legacy corpus

`temp/wakeword/batch-smoke-001/generation` was repacked without TTS or changes to original feature bytes. Its extracted-model hashes/feature recipe match files/resource-profile.json. The portable ZIP contains exactly manifest.json and four feature arrays, never WAV/review/ACAV/PT. Old generated folders remain usable through the adapter. Initial migration ZIP/corpus hashes predate the addition of aggregate review_summary; validation.json records the synthetic control identity separately.

## Recovery and contract evidence

- New generation entry point executes existing Parler/Vosk/batch/crop code with the integration fixture, packages four parts, preserves review, never calls trainer, and reuses completion without additional TTS. Existing 3N/confidence/review/durable batching tests run against canonical generation.
- Wrong word, insufficient original positives, NaN/Inf/dtype/shape/hash/overlapping lineage/review contamination, archive links/path/case/budget failures reject before accepted training. Float32 big endian finite scanning is tested. Payload allowlists exclude audio/background/PT.
- Stable job IDs are persisted before add; a lost post-commit response reconciles that ID. Transport-unknown never resubmits. Partial optimizer requires a new output; native late selection/export/evaluation/report faults recover with unchanged update/history hashes.
- Dataset cache upload is explicit and streaming. Job arguments receive a bare cache name and expected corpus_id, never an absolute host dataset path or ZIP bytes. This is required because current api.add does not upload FileLike paths automatically.
- Local complete works with remote readiness forbidden. Expired cache triggers a separate export attempt, not training. Cache-path reuse is followed by real hash/presence checks. Model/snapshot/request/execution identities and exact output allowlist are verified.
- Prepare check-only is read-only; unregistered server returns update/restart instruction. Explicit installation repairs resources even if installation.yaml already exists. Live installation/repair still awaits Docker/resource capacity.

## Requirement evidence matrix

“Local pass” means the stated native/contract coverage, not remote acceptance.

| Requirement | Evidence/status |
|---|---|
| FR-001 | Canonical independent Chara generation and remote-training orchestration; local pass; remote pending |
| FR-002 | Preserved generation algorithms and existing integration tests; real Parler/Vosk pending |
| FR-003 | Existing confidence/3N/review/batch/reconciliation tests pass |
| FR-004 | Feature-only packaging, actual originals/rows, hashes and aggregate review; local pass |
| FR-005 | Exact five-member ZIP, no re-augmentation in trainer; local pass |
| FR-006 | New installer/profile/splits/repair/hash checks implemented; actual ACAV install pending |
| FR-007 | No background in uploaded payload; two corpora reuse unchanged fixture background without downloads |
| FR-008 | Explicit independent requirements, immutable request and surplus preservation; local pass |
| FR-009 | Stdlib header/hash/finite/lineage/original-count/target preflight; local pass |
| FR-010 | Server repeats checks and isolates safe ZIP extraction; local pass |
| FR-011 | Explicit cache/FileLike upload implementation and stream contracts pass; real remote HTTP pending |
| FR-012 | Real local CPU training/export/parity path passes; Docker execution pending; Chara still needs base NumPy, see below |
| FR-013 | Numeric regression and three actual updates/stages; full remote curriculum pending |
| FR-014 | Final ONNX ORT scores and raw window/exposure metadata; local pass |
| FR-015 | Both reports from real numeric measurements, portable source checks; local pass |
| FR-016 | Streamed portable download/identity checks and offline no-PT/no-inference rebuild; local pass |
| FR-017 | Python prepare/generate/train/report and Make removal; live prepare pending |
| FR-018 | Orchestration methods show stages; one canonical numeric implementation; inspected |
| FR-019 | Lost-response/offline/mismatch/lock/native cache tests; remote fault injection pending |
| FR-020 | Native partial/late faults and independent cache re-export; remote fault injection pending |
| FR-021 | Main/smoke/training presets and README/quickstart updated; comments excluded from numeric config |
| SC-001 | Integration-fixture generation passes; real generation pending T018 |
| SC-002 | Native CPU ONNX/reports pass; isolated remote machine pending T037 |
| SC-003 | Negative contract cases pass; exhaustive remote rejection pending |
| SC-004 | Two distinct synthetic corpora, shared background, downloads forbidden: pass in stated local scope |
| SC-005 | Verified portable model/metrics, blocked-inference offline report rebuild: local pass |
| SC-006 | Native fault/reconciliation/cache tests pass; remote recovery pending T046 |
| SC-007 | CLI help/wrappers/imports pass; live Docker prepare pending |
| SC-008 | Local regression and measured native toy runs pass; full remote recipe pending T050 |

## Limits and design corrections

- `docker info` fails to connect to `//./pipe/dockerDesktopLinuxEngine` (“The system cannot find the file specified”). Docker image build, native Linux self-test, Parler/Vosk live generation and remote acceptance have **not run**. Do not equate successful Windows core tests with them.
- Drive D free space at inspection:20,568,506,368 bytes (~19.2GiB). ACAV installer requires at least21GiB free in the server resource filesystem during preparation; current D would fail that explicit preflight. No user data was deleted to make space.
- Chara/Avatar's existing package imports load NumPy. Archive/config/validation imports are stdlib-only and orchestration does not load Torch/ORT/ONNX/openwakeword. A strictly NumPy-free Chara process would require changing common modules, excluded by the user/plan; that stronger infrastructure interpretation remains unsupported.
- Canonical corpus identity excludes host resource paths/timestamps; transport SHA is separate. Immutable server result manifests survive local HTML regeneration via local-render.json.
- Background preparation is in the decider installer; numeric background resolution remains core/inputs.py. Result packaging is core/portable_results.py rather than a redundant app/result_export.py. Wrappers preserve import/patch identity and static typing.
- Main generation presets/default resources no longer download ACAV on the host. Existing host ACAV data is retained; prepare reuses verified augmentation resources. Legacy explicit ACAV preprocessing remains supported for old callers/tests, while training uses its server installer.
- Failure diagnostics follow neighbouring marshalling services (stage/reason exception text). The vocabulary in the contract is diagnostic classification, not a new framework error transport.


## Architecture correction — 2026-11-18

User clarified that only the training implementation belongs in BrainBox. Canonical orchestration now lives directly in chara/wakeword/generation_pipeline.py and training_pipeline.py; supporting generation/transfer/environment/CLI modules live under chara/wakeword. Numeric training/runtime code lives inside brainbox/deciders/voice_analysis/wakeword_training/runtime. The image builder stages that runtime directly, without importing Chara. Previous brainbox.pipelines.wakeword imports have been removed; use python -m chara.wakeword.scripts.prepare/generate/train/report for new launches. Historical acceptance evidence above refers to the previous layout.

Migration validation: full wakeword regression passed (100 tests, 86.805s, no skips). Ruff passed on both canonical implementations and compatibility wrappers. mypy passed on 150 source files. The staged decider runtime/service imported with Chara prohibited under both existing Python 3.11 and 3.12 environments. New Chara and deprecated BrainBox CLI help commands passed. No Docker rebuild/install or retraining was performed for this layout correction.


2026-11-18: removed obsolete brainbox/pipelines compatibility aliases and duplicate requirement files. All active callers use Chara orchestration or the decider runtime. Historical commands above describe the earlier layout.

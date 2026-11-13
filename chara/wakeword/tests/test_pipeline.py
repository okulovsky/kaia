import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
try:
    import numpy as np
    import soundfile as sf
    from chara import Chara
    from wakeword.generation.pipeline import run
    from wakeword.generation.settings import GenerationSettings
    from wakeword.generation.validation import FEATURES, check_completed
except ImportError:
    np = None


class Cache:
    def __init__(self):
        self.files = {}

    def upload(self, name, source):
        self.files[name] = Path(source).read_bytes()

    def read(self, name):
        return self.files[name]

    def open(self, name):
        yield self.files[name]


class FakeBrainBox:
    def resources(self, decider):
        return SimpleNamespace(read=lambda name: b"mini-v1: fixture\nen: fixture\n")

    def __init__(self):
        self.cache = Cache()
        self.jobs = self
        self.batches = self
        self.submissions = []
        self.job_batches = {}
        self.completed = {}
        self.voices = {}
        self.tts_calls = 0
        self.deciders = []
        self.calls = 0
        self.reject_once = True
        self.fail_vosk_once = False
        self.reject_always = False
        self.fail_negative_always = False
        self.fail_normalization_once = False
        self.normalization_sizes = []
        self.feature_failures = 0
        self.feature_calls = 0
        self.oom_once = False

    def audio(self):
        output = io.BytesIO()
        sf.write(
            output,
            np.sin(np.arange(24000) * 0.01) * 0.2,
            16000,
            format="WAV",
            subtype="PCM_16",
        )
        return output.getvalue()

    def archive(self, files, manifest):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
            archive.writestr("manifest.json", json.dumps(manifest))
        name = uuid4().hex + ".zip"
        self.cache.files[name] = output.getvalue()
        return name

    def get_job(self, identity):
        if identity not in self.completed:
            raise ValueError("Can't find a job with id " + identity)
        self.completed[identity].id = identity
        self.completed[identity].batch = self.job_batches.get(identity)
        return self.completed[identity]

    def get_jobs(self, ids):
        return [self.get_job(identity) for identity in ids]

    def get_batch_progress(self, batch_id):
        ids = [
            identity
            for identity, batch in self.job_batches.items()
            if batch == batch_id
        ]
        return SimpleNamespace(
            is_finished=all(self.completed[identity].finished for identity in ids)
        )

    def base_add(self, descriptions):
        self.submissions.append([job.id for job in descriptions])
        for job in descriptions:
            self.job_batches[job.id] = job.batch
        for job in descriptions:
            self.calls += 1
            self.deciders.append(job.decider)
            method = job.method
            args = job.arguments
            if method == "voiceover_with_description":
                self.tts_calls += 1
                if self.fail_negative_always and not args["text"].startswith("Hi "):
                    self.completed[job.id] = SimpleNamespace(
                        finished=True, error="synthesis failed", result=None
                    )
                    continue
                if self.oom_once:
                    self.oom_once = False
                    self.completed[job.id] = SimpleNamespace(
                        finished=True, error="CUDA out of memory", result=None
                    )
                    continue
                result = uuid4().hex + ".wav"
                self.cache.files[result] = self.audio()
                self.voices[result] = args["text"][3:-4]
            elif method == "transcribe_to_array":
                if self.fail_vosk_once:
                    self.fail_vosk_once = False
                    raise ConnectionError("offline before submission")
                confidence = 0.69 if self.reject_once or self.reject_always else 0.9
                self.reject_once = False
                result = [
                    {"word": "hi", "start": 0.1, "end": 0.3, "conf": 1},
                    {
                        "word": self.voices[args["file"]],
                        "start": 0.5,
                        "end": 0.9,
                        "conf": confidence,
                    },
                    {"word": "go", "start": 1.1, "end": 1.3, "conf": 1},
                ]
            else:
                raise AssertionError(method)
            self.completed[job.id] = SimpleNamespace(
                finished=True, error=None, result=result
            )


@unittest.skipIf(np is None, "requires the kaia environment")
class PipelineTests(unittest.TestCase):
    def setUp(self):
        from wakeword.generation.pipeline import WakewordPipeline

        original = WakewordPipeline._normalize

        def normalize(pipeline, cases):
            fake = Chara.Apis.brainbox_api
            fake.normalization_sizes.append(len(cases))
            if fake.fail_normalization_once and cases:
                fake.fail_normalization_once = False
                rejected = cases[0]
                rejected.error = "bad source"
                rejected.error_stage = "normalize"
                rejected.reason_code = "invalid_audio"
                return [rejected] + original(pipeline, cases[1:])
            return original(pipeline, cases)

        def features(pipeline, cases, resources):
            fake = Chara.Apis.brainbox_api
            fake.feature_calls += 1
            if fake.feature_failures:
                fake.feature_failures -= 1
                raise RuntimeError("temporary embedding failure")
            folder = Chara.current.folder
            for name in FEATURES:
                np.save(
                    folder / (name + ".npy"), np.ones((2, 16, 96), dtype=np.float32)
                )
            return folder

        def resources(settings):
            from wakeword.generation.resources import read_voice_models

            return {
                "resources": [],
                "versions": {},
                "voice_models": read_voice_models(settings),
            }

        for target, kwargs in [
            (
                "wakeword.generation.pipeline.prepare_resources",
                {"side_effect": resources},
            ),
            (
                "wakeword.generation.pipeline.WakewordPipeline._normalize",
                {"new": normalize},
            ),
            (
                "wakeword.generation.pipeline.WakewordPipeline._features",
                {"new": features},
            ),
            ("wakeword.generation.pipeline.ResourceInstaller", None),
            (
                "wakeword.generation.negatives.pipeline.generate_negative_texts",
                {"return_value": ["commuter", "compost"]},
            ),
        ]:
            if kwargs is None:
                continue
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch(
            "wakeword.generation.local.resources.ResourceInstaller.load",
            return_value={"resources": [], "versions": {}},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_negative_budget_survives_resume_with_individual_parler_jobs(self):
        fake = FakeBrainBox()
        fake.reject_once = False
        fake.fail_negative_always = True
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "run"
            settings = GenerationSettings("computer", ["computer"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                for _ in range(2):
                    with self.assertRaises(RuntimeError):
                        run(settings, folder)
                    self.assertEqual(fake.tts_calls, 10)
            progress = json.loads(
                (folder / "generation_state/negative_train/progress.json").read_text()
            )
            self.assertEqual(len(progress["attempts"]), 6)
            self.assertEqual(len({a["task_id"] for a in progress["attempts"]}), 6)
            self.assertEqual(len(list((folder / "review").glob("*/record.json"))), 6)

    def test_common_failure_stops_and_manual_resume_keeps_successes(self):
        fake = FakeBrainBox()
        fake.reject_once = False
        fake.oom_once = True
        with tempfile.TemporaryDirectory() as temporary:
            settings = GenerationSettings("computer", ["computer"], [])
            folder = Path(temporary) / "run"
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                with self.assertRaises(RuntimeError):
                    run(settings, folder)
                self.assertEqual(fake.tts_calls, 2)
                result = run(settings, folder)
            self.assertEqual(result.status, "complete")
            self.assertEqual(fake.tts_calls, 9)

    def test_processing_retry_preserves_source_budget(self):
        fake = FakeBrainBox()
        fake.reject_once = False
        fake.feature_failures = 1
        with tempfile.TemporaryDirectory() as temporary:
            settings = GenerationSettings("computer", ["computer"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                result = run(settings, Path(temporary) / "run")
            self.assertEqual(result.status, "complete")
            self.assertEqual(fake.feature_calls, 2)
            self.assertEqual(fake.tts_calls, 8)

    def test_resume_after_processing_retries_exhausted(self):
        fake = FakeBrainBox()
        fake.reject_once = False
        fake.feature_failures = 3
        with tempfile.TemporaryDirectory() as temporary:
            settings = GenerationSettings("computer", ["computer"], [])
            folder = Path(temporary) / "run"
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                with self.assertRaises(RuntimeError):
                    run(settings, folder)
                self.assertEqual(fake.feature_calls, 3)
                result = run(settings, folder)
            self.assertEqual(result.status, "complete")
            self.assertEqual(fake.feature_calls, 4)
            self.assertEqual(fake.tts_calls, 8)

    def test_exhausted_budget_remains_exhausted_after_resume(self):
        fake = FakeBrainBox()
        fake.reject_always = True
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "run"
            settings = GenerationSettings("computer", ["computer"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                for _ in range(2):
                    with self.assertRaises(RuntimeError):
                        run(settings, folder)
                    self.assertEqual(fake.tts_calls, 6)
                self.assertEqual(
                    len(list((folder / "review").glob("*/record.json"))), 6
                )
                self.assertFalse((folder / "dataset/manifest.json").exists())

    def test_late_rejection_replaces_only_failed_source(self):
        fake = FakeBrainBox()
        fake.reject_once = False
        fake.fail_normalization_once = True
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "run"
            settings = GenerationSettings("computer", ["computer"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                run(settings, folder)
            self.assertEqual(fake.tts_calls, 9)
            self.assertEqual(fake.normalization_sizes, [8, 1])
            manifest = check_completed(folder / "dataset")
            rejected = {
                p.parent.name for p in (folder / "review").glob("*/record.json")
            }
            self.assertFalse(rejected & {c["sample_id"] for c in manifest["lineage"]})

    def test_complete_review_and_cached_repeat(self):
        fake = FakeBrainBox()
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "run"
            settings = GenerationSettings("computer", ["computer", "computers"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                result = run(settings, folder)
                self.assertEqual(result.status, "complete")
                self.assertNotIn("WakewordData", fake.deciders)
                self.assertEqual(fake.deciders.count("ParlerTts"), fake.tts_calls)
                check_completed(folder / "dataset")
                self.assertEqual(
                    len(list((folder / "review").glob("*/record.json"))), 1
                )
                count = fake.tts_calls
                run(settings, folder)
                self.assertEqual(fake.tts_calls, count)
                settings.min_vosk_confidence = 0.8
                with self.assertRaises(ValueError):
                    run(settings, folder)
                settings.min_vosk_confidence = 0.7
                (folder / "dataset/manifest.json").unlink()
                with self.assertRaises(ValueError):
                    run(settings, folder)
                self.assertEqual(fake.tts_calls, count)

    def test_resume_after_voiceover_does_not_repeat_tts(self):
        fake = FakeBrainBox()
        fake.fail_vosk_once = True
        fake.reject_once = False
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "run"
            settings = GenerationSettings("computer", ["computer"], [])
            with patch.object(Chara, "Apis", SimpleNamespace(brainbox_api=fake)):
                with self.assertRaisesRegex(Exception, "Can't find a job with id"):
                    run(settings, folder)
                self.assertEqual(fake.tts_calls, 2)
                result = run(settings, folder)
                self.assertEqual(result.status, "complete")
                self.assertEqual(fake.tts_calls, 8)

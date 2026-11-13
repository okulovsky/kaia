from pathlib import Path

from brainbox.deciders import ParlerTts, Vosk

from chara import BrainBoxCasePipeline, CaseCollection, Chara, Language

from ..brainbox_execution import DurableCasePipeline
from ..review import save_review
from .verification import RejectedAudio, verify


class PositiveAudioPipeline:
    def __init__(self, settings, run_folder):
        self.settings = settings
        self.run_folder = Path(run_folder)
        self.recognition_attempt = 0

    def _voiceover_task(self, case):
        return ParlerTts.new_task(
            id=case.task_ids["voiceover"]
        ).voiceover_with_description(
            self.settings.prefix + case.text + self.settings.suffix,
            case.voice_description,
            model="mini-v1",
            seed=case.seed,
        )

    def _recognition_task(self, case):
        from uuid import NAMESPACE_URL, uuid5

        task_id = str(
            uuid5(
                NAMESPACE_URL,
                case.sample_id + "/recognition/" + str(self.recognition_attempt),
            )
        )
        case.task_ids["recognition"] = task_id
        return Vosk.new_task(id=task_id).transcribe_to_array(
            case.source_audio.name,
            Language.from_code(self.settings.language_code).vosk_name,
        )

    def voiceover(self, cases):
        return DurableCasePipeline(
            self._voiceover_task, "source_audio", result_to_file=True
        )(cases)

    def recognition(self, cases):
        return DurableCasePipeline(
            self._recognition_task,
            "recognition",
            uploader=BrainBoxCasePipeline.Uploader(
                lambda c: c.source_audio, remove_after=False
            ),
        )(cases)

    def cut(self, cases):
        import soundfile as sf

        folder = Chara.current.folder / "samples"
        folder.mkdir(parents=True, exist_ok=True)
        for case in cases.cases:
            if case.error:
                case.reason_code = case.reason_code or "processing_failed"
                case.error_stage = case.error_stage or (
                    "recognition" if case.source_audio else "voiceover"
                )
                save_review(self.run_folder, case)
                continue
            try:
                with sf.SoundFile(case.source_audio) as source:
                    crop = verify(
                        case.text,
                        case.recognition,
                        len(source) / source.samplerate,
                        self.settings.prefix,
                        self.settings.suffix,
                        self.settings.min_vosk_confidence,
                        self.settings.target_variants,
                    )
                    source.seek(round(crop.start * source.samplerate))
                    audio = source.read(
                        round((crop.end - crop.start) * source.samplerate)
                    )
                    if len(audio) == 0:
                        raise RejectedAudio("invalid_crop", "empty crop")
                    path = folder / (case.sample_id + ".wav")
                    sf.write(path, audio, source.samplerate, subtype="PCM_16")
                case.crop_audio = path
                case.state = "accepted_crop"
                case.verification = crop
            except (RejectedAudio, RuntimeError, OSError, ValueError) as error:
                case.error = str(error)
                case.reason_code = getattr(error, "reason", "invalid_audio")
                case.error_stage = "cut"
                save_review(self.run_folder, case)
        return CaseCollection(cases)

    def __call__(self, cases):
        cases = Chara.call(self.voiceover)(cases)
        self.recognition_attempt = 0
        cases = Chara.call(self.recognition)(cases)
        for attempt in (1, 2):
            retry = [c for c in cases.errors if c.source_audio is not None]
            if not retry:
                break
            unchanged = [c for c in cases.cases if c not in retry]
            for case in retry:
                case.error = None
            self.recognition_attempt = attempt
            repeated = Chara.call(self.recognition, f"recognition_retry_{attempt}")(
                CaseCollection(retry)
            )
            cases = CaseCollection(unchanged, repeated)
        return Chara.call(self.cut)(cases)


class PositiveCollection:
    def __init__(self, settings, run_folder, excluded_ids=()):
        self.settings = settings
        self.run_folder = Path(run_folder)
        self.excluded_ids = set(excluded_ids)

    def make_pipeline(self):
        return PositiveAudioPipeline(self.settings, self.run_folder)

    def make_case(self, group, item):
        from .case import create_case

        return create_case(self.settings, group, item)

    def __call__(self, group):
        from ..progress import AttemptLedger, IncompleteGeneration

        target = self.settings.counts[group]
        ledger = AttemptLedger(
            self.run_folder / "generation_state" / group, target, group
        )
        ledger.data.setdefault("batches", [])
        assigned = {
            item["sample_id"] for batch in ledger.data["batches"] for item in batch
        }
        orphans = [
            dict(item)
            for item in ledger.data["attempts"]
            if item["sample_id"] not in assigned
        ]
        if orphans:
            ledger.data["batches"].append(orphans)
            ledger.save()
        accepted = []
        pipeline = self.make_pipeline()
        batch_index = 0
        while len(accepted) < target:
            if batch_index < len(ledger.data["batches"]):
                attempts = ledger.data["batches"][batch_index]
            else:
                remaining = 3 * target - len(ledger.data["attempts"])
                size = min(self.settings.batch_size, target - len(accepted), remaining)
                if size <= 0:
                    raise IncompleteGeneration(
                        f"{group}: only {len(accepted)}/{target} accepted after {3 * target} attempts; see review"
                    )
                from ..settings import GROUPS

                offset = sum(
                    3 * self.settings.counts[g] for g in GROUPS[: GROUPS.index(group)]
                )
                start = len(ledger.data["attempts"])
                attempts = [
                    dict(item)
                    for item in ledger.reserve_many(
                        [self.settings.seed + offset + start + i for i in range(size)]
                    )
                ]
                ledger.data["batches"].append(attempts)
                ledger.save()
            cases = CaseCollection(self.make_case(group, item) for item in attempts)
            result = Chara.call(pipeline, f"batch_{batch_index:04d}")(cases)
            accepted.extend(
                c for c in result.successes if c.sample_id not in self.excluded_ids
            )
            ids = {case.sample_id for case in result.successes}
            rejected = {case.sample_id for case in result.errors}
            for item in ledger.data["attempts"]:
                if item["sample_id"] in ids:
                    item["state"] = "accepted"
                elif item["sample_id"] in rejected:
                    item["state"] = "review"
            ledger.save()
            fatal = next(
                (
                    c.error
                    for c in result.errors
                    if any(
                        token in c.error.lower()
                        for token in (
                            "not installed",
                            "no such file",
                            "out of memory",
                            "unsupported language",
                        )
                    )
                ),
                None,
            )
            if fatal and not attempts[0].get("fatal_reported"):
                attempts[0]["fatal_reported"] = True
                ledger.save()
                raise RuntimeError(
                    f"{group}: common worker failure; fix the resource and resume: {fatal}"
                )
            batch_index += 1
        return CaseCollection(accepted)

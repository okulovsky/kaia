from brainbox.deciders import ParlerTts

from chara import Chara

from ..positives.case import create_case
from ..positives.pipeline import PositiveAudioPipeline, PositiveCollection
from ..review import save_review


def generate_negative_texts(settings, resources, count):
    from ..local.texts import generate_negative_texts as generate

    return generate(settings, resources, count)


class NegativeAudioPipeline(PositiveAudioPipeline):
    def _voiceover_task(self, case):
        return ParlerTts.new_task(
            id=case.task_ids["voiceover"]
        ).voiceover_with_description(
            case.text, case.voice_description, model="mini-v1", seed=case.seed
        )

    def __call__(self, cases):
        cases = Chara.call(self.voiceover)(cases)
        for case in cases.cases:
            if case.error:
                case.error_stage = "voiceover"
                case.reason_code = "processing_failed"
                save_review(self.run_folder, case)
            else:
                case.crop_audio = case.source_audio
                case.state = "accepted"
        return cases


class NegativeCollection(PositiveCollection):
    def __init__(self, settings, resources, run_folder, excluded_ids=()):
        super().__init__(settings, run_folder, excluded_ids)
        self.resources = resources

    def __call__(self, group):
        self.texts = Chara.call(generate_negative_texts, "texts")(
            self.settings, self.resources, self.settings.counts[group]
        )
        if not self.texts:
            raise ValueError(
                "negative text generator produced no phrases different from target"
            )
        return super().__call__(group)

    def make_pipeline(self):
        return NegativeAudioPipeline(self.settings, self.run_folder)

    def make_case(self, group, item):
        case = create_case(self.settings, group, item)
        case.text = self.texts[item["index"] % len(self.texts)]
        return case

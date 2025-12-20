from avatar.server import AvatarApi, AvatarServerSettings
from avatar.server.components import ResourcesComponent
from avatar.daemon import ParaphraseService, State, PlayableTextMessage, UtteranceSequenceCommand, TextInfo
from unittest import TestCase
from grammatron import Template, TemplatesCollection, TimedeltaDub
from chara.paraphrasing.utterances import CaseBuilder, UtteranceParaphrasePipeline, UtteranceParaphrasesCache, ParaphraseStats
from chara.paraphrasing.common import ParaphrasePipeline, ParaphraseCache, ParaphraseCase
from foundation_kaia.misc import Loc
from chara.common import CharaApis



class Utterances(TemplatesCollection):
    yes = Template("yes")
    timer_is_set = Template(f"The timer is set for {TimedeltaDub().as_variable('duration')}")



def first_run(cache: ParaphraseCache, cases: list[ParaphraseCase]):
    if len(cases) != 1:
        raise AssertionError("Expected exactly 1 case")
    if cases[0].template.template.get_name().endswith('yes'):
        option = 'Sure!'
    else:
        option = "Timer's ticking for {duration}"
    cache.write_result([
        ParaphrasePipeline.case_and_option_to_record(cases[0], option)
    ])

def second_run(cache: ParaphraseCache, cases: list[ParaphraseCase]):
    if len(cases) != 1:
        raise AssertionError("Expected exactly 1 case")
    cache.write_result([
        ParaphrasePipeline.case_and_option_to_record(cases[0], "Yep!")
    ])



class UtteranceParaphrasePipelineTestCase(TestCase):
    def check_stats(self, stats: list[ParaphraseStats], yes_existing, yes_seen, timer_existing, timer_seen):
        for s in stats:
            if s.case.template.template.get_name().endswith('yes'):
                self.assertEqual(yes_existing, s.existing)
                self.assertEqual(yes_seen, s.seen)
            else:
                self.assertEqual(timer_existing, s.existing)
                self.assertEqual(timer_seen, s.seen)



    def test_pipeline(self):
        buider = CaseBuilder(Utterances.get_templates())
        with Loc.create_test_folder() as resources_folder:
            settings = AvatarServerSettings((
                ResourcesComponent(resources_folder),
            ))

            with AvatarApi.Test(settings) as api:
                CharaApis.avatar_api = api
                with Loc.create_test_folder() as folder_1:
                    cache = UtteranceParaphrasesCache(folder_1)
                    pipe = UtteranceParaphrasePipeline(buider, first_run, 2, 1)
                    pipe(cache)

                    stats = cache.stats.read()
                    self.check_stats(stats, 0, 0, 0, 0)

                state = State(None, None, None, 'en')
                service = ParaphraseService(state)
                service.set_resources_folder(resources_folder/'ParaphraseService')
                service.on_initialize(None)
                result = service.paraphrase(PlayableTextMessage(UtteranceSequenceCommand(
                    Utterances.yes()
                ), TextInfo(None, 'en')))
                self.assertEqual('Sure!', result.text.utterances_sequence.utterances[0].to_str())

                with Loc.create_test_folder() as folder_2:
                    cache = UtteranceParaphrasesCache(folder_2)
                    pipe = UtteranceParaphrasePipeline(buider, second_run, 1, 1)
                    pipe(cache)

                    stats = cache.stats.read()
                    self.check_stats(stats, 1, 1, 1, 0)
                    result = cache.batches.create_subcache(0).read_result()
                    self.assertEqual(
                        Utterances.yes.get_name(),
                        result[0].original_template_name
                    )













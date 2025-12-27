from chara.voice_clone.exploring import VoiceVoiceCloneCache
from chara.common import Samples, Language, logger, CharaApis
from chara.voice_clone.common import XTTSTrain, XTTSInference, ZonosTrain, ZonosInference, ChatterboxTrain, ChatterboxInference
from brainbox import BrainBox
from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common.tools import Wav
from pathlib import Path

class VoiceClonersTestCase(TestCase):
    def test_voice_cloners(self):
        cloners = [
            ('xtts', XTTSTrain(), XTTSInference()),
            ('zonos', ZonosTrain(), ZonosInference()),
            ('chatterbox', ChatterboxTrain(), ChatterboxInference()),
        ]
        text = list(Language.English().sample_text)

        data = Wav.List()
        with BrainBox.Api.Test() as api:
            CharaApis.brainbox_api = api
            with Loc.create_test_folder() as folder:
                for name, train, inference in cloners:
                    cache = VoiceCloneCache(folder/name)
                    cache.pipeline(
                        Samples.lina,
                        train,
                        text,
                        inference
                    )
                    result = cache.read_result()
                    result.assign_metakey('model_name', name)
                    data += result


                with logger.html_report(Path(__file__).parent/"voice_cloners.html"):
                    logger.log(
                        data.draw().group('model_name').group('split').blocks().widget()
                    )



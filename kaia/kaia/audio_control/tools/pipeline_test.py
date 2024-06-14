from kaia.kaia.audio_control import core, setup
from kaia.infra import Loc
from datetime import datetime
from pathlib import Path

def _echo(x):
    return x

class PipelineTest:
    def __init__(self,
                 settings: setup.AudioControlSettings,
                 test_duration_in_seconds
                 ):
        self.settings = settings
        self.test_duration_in_seconds = test_duration_in_seconds




    def __call__(self):
        input, output = self.settings.create_input_and_output()

        control = core.AudioControl(
            input,
            output,
            setup.PorcupinePipeline('wakeup', 'open', 'listen'),
            [
                setup.BuffererPipeline(
                    'listen',
                    self.settings.create_bufferer_pipeline_settings(),
                    'close',
                    _echo,
                    None
                )
            ],
            {
                'open': self.settings.awake_template,
                'close': self.settings.confirmed_template
            },
            0,
            core.ConsoleControlDebugConsole()
        )

        begin = datetime.now()
        while True:
            if (datetime.now() - begin).total_seconds() > self.test_duration_in_seconds:
                break
            result = control.iteration()
            if result.processed_input is not None and result.processed_input.collected_data is not None:
                control.play_requests_queue.put(core.AudioSampleTemplate(result.processed_input.collected_data).to_sample())


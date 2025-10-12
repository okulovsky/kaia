from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, BrainBoxExtendedTask, MediaLibrary
)
from .settings import ResemblyzerSettings
from pathlib import Path


class ResemblyzerController(DockerWebServiceController[ResemblyzerSettings], INotebookableController):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.8.20',
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 8084}
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return ResemblyzerSettings()

    def create_api(self):
        from .api import Resemblyzer
        return Resemblyzer()


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Resemblyzer

        model_name = 'test'
        media_library_path = Path(__file__).parent / 'test_media_library.zip'
        prerequisites = Resemblyzer.upload_dataset(model_name, media_library_path, False)


        api.execute(BrainBoxExtendedTask(
            BrainBoxTask.call(Resemblyzer).train(model_name),
            prerequisite=prerequisites
        ))

        yield (TestReport
               .last_call(api)
               .href('train')
               .with_comment("Training the model with pre-uploaded resources")
               )

        media_library = MediaLibrary.read(media_library_path)

        first_time = True
        first_file = None
        for record in media_library.records:
            if record.tags['split'] == 'test':
                file = record.get_file()
                result = api.execute(BrainBoxTask.call(Resemblyzer).classify(file, model_name))
                if first_time:
                    first_file = file
                    yield TestReport.last_call(api).href('inference').with_comment("Running inference with trained model")
                first_time = False
                tc.assertEqual(record.tags['speaker'], result)

        api.execute(BrainBoxTask.call(Resemblyzer).distances(first_file,model_name))
        yield TestReport.last_call(api).href('distances')

        for record in media_library.records:
            file = record.get_file()
            result = api.execute(BrainBoxTask.call(Resemblyzer).vector(file))
            yield TestReport.last_call(api).href('vectorization').with_comment('Getting a vector of a voice file without ')



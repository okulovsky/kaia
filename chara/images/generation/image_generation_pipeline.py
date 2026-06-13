import json
from pathlib import Path
from typing import Callable, Any

from .scenarios import ImageScenarioPipeline, ImageScenarioCase
from .drawing import DrawingPipeline, DrawingCase
from chara.common import Chara, CaseCollection
from foundation_kaia.marshalling import Serializer, File
from avatar.daemon.image_service.media_library import MediaLibrary


class ImageGenerationPipeline:
    def __init__(self,
                 scenarios: ImageScenarioPipeline,
                 drawing: DrawingPipeline,
                 filters: dict[str, Callable[[DrawingCase], bool]]
                 ):
        self.scenarios = scenarios
        self.drawing = drawing
        self.filters = filters

    def __call__(self, cases: CaseCollection[ImageScenarioCase]) -> Path:
        cases = Chara.call(self.scenarios, 'scenarios')(cases).raise_if_all_errors()
        cases = [DrawingCase(c) for c in cases.successes]
        cases = Chara.call(self.drawing, 'drawing')(CaseCollection(cases)).raise_if_all_errors()

        @Chara.phase
        def filtering():
            final_cases = []
            for case in cases.cases:
                for name, filter in self.filters.items():
                    if not filter(case):
                        case.error = f"Rejected by filter {name}"
                        final_cases.append(case)
            return final_cases

        final_cases = Chara.previous.result

        ml_path = Chara.current.folder/'media_library.zip'
        self.to_media_library(final_cases, ml_path)

        return ml_path



    def to_media_library(self, final_cases: list[DrawingCase], output_path: Path):
        scenario_serializer = Serializer.parse(list[Any])

        records = []
        files = []
        for case in final_cases:
            scenario = case.scenario
            tags = {}
            if isinstance(scenario, ImageScenarioCase):
                tags['character'] = scenario.character.name
                if scenario.theme is not None:
                    tags['theme'] = scenario.theme.name
                if scenario.activity is not None:
                    tags['activity'] = scenario.activity
            records.append(MediaLibrary.Record(path=case.image.name, tags=tags))
            files.append(case.image)

        scenarios = [case.scenario for case in final_cases]
        full_descriptions = json.dumps(scenario_serializer.to_json(scenarios), indent=2).encode()
        files.append(File('full_descriptions.json', full_descriptions))

        MediaLibrary.save(output_path, records, files)



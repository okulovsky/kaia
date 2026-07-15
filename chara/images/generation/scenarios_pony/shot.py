from copy import deepcopy
from .case import ImageScenarioCase, Shot
from typing import Iterable
from chara.common import CaseCollection

BACK_VIEW = 'from behind, looking back'
COWBOY = 'cowboy shot'

class ShotPipeline:
    def __init__(self,
                 framings: Iterable[str|None] = ('full body picture', COWBOY),
                 character_angles: Iterable[str|None] = ('frontal view', 'side view', BACK_VIEW),
                 camera_angles: Iterable[str|None] = (None, 'high angle', 'low angle'),
                 ):
        self.framings = framings
        self.character_angles = character_angles
        self.camera_angles = camera_angles

    def is_back_view(self, shot):
        return shot.character_angle == BACK_VIEW

    def are_feet_visible(self, shot):
        return shot.framing != COWBOY

    def are_legs_visible(self, shot):
        return True

    def apply_shot(self, case: ImageScenarioCase, shot: Shot):
        case.shot = shot
        if not self.are_feet_visible(shot):
            case.clothing.footwear = None
        if not self.are_legs_visible(shot):
            case.clothing.bottom = None

    def __call__(self, cases: CaseCollection[ImageScenarioCase]) -> CaseCollection[ImageScenarioCase]:
        result = []
        for case in cases.successes:
            for framing in self.framings:
                for character_angle in self.character_angles:
                    for camera_angle in self.camera_angles:
                        shot = Shot(framing, character_angle, camera_angle)
                        new_case = deepcopy(case)
                        self.apply_shot(new_case, shot)
                        result.append(new_case)
        return CaseCollection(result)




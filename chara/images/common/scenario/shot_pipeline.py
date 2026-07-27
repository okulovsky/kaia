import random
from copy import deepcopy
from .shot import Shot
from .image_scenario import IImageScenario
from typing import Iterable
from chara.common import CaseCollection

FRAMINGS = [
    Shot.Framing('full body picture', True, True),
    Shot.Framing('cowboy shot', True, False)
]

ANGLES = [
    Shot.CharacterAngle('frontal view', False, True),
    Shot.CharacterAngle('side, profile view', False, False),
    Shot.CharacterAngle('view from behind, looking back', True, False)
]

CAMERA_ANGLES = [None, 'low camera angle', 'high camera angle']

class ShotPipeline:
    def __init__(self, count: int|None = None):
        self.count = count

    def apply_shot(self, case: IImageScenario, shot: Shot):
        case.shot = shot
        if not shot.feet_visible:
            case.clothing.footwear = None
        if not shot.legs_visible:
            case.clothing.bottom = None

    def _get_options(self):
        result = []
        for angle in ANGLES:
            framing = random.choice(FRAMINGS)
            camera_angle = random.choice(CAMERA_ANGLES)
            result.append(Shot(framing, angle, camera_angle))
        return result


    def __call__(self, cases: CaseCollection[IImageScenario]) -> CaseCollection[IImageScenario]:
        result = []
        for case in cases.successes:
            shots = self._get_options()

            if self.count is not None and self.count < len(shots):
                shots = random.sample(shots, self.count)

            for shot in shots:
                new_case = deepcopy(case)
                self.apply_shot(new_case, shot)
                result.append(new_case)

        return CaseCollection(result)




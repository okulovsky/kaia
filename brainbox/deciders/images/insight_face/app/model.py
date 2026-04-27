from dataclasses import dataclass, field
from typing import Tuple

from foundation_kaia.brainbox_utils import Installer


@dataclass
class InsightFaceModelSpec:
    det_size: Tuple[int, int] = field(default_factory=lambda: (320, 320))


class InsightFaceInstaller(Installer[InsightFaceModelSpec]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: InsightFaceModelSpec):
        from processing import FaceEmbedder
        FaceEmbedder(model_name=model, det_size=model_spec.det_size)

    def _execute_model_loading(self, model: str, model_spec: InsightFaceModelSpec):
        from processing import FaceEmbedder
        return FaceEmbedder(model_name=model, det_size=model_spec.det_size)

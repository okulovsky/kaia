from dataclasses import dataclass
from enum import Enum


class YoloModels(str, Enum):
    yolov8_face = 'arnabdhar/YOLOv8-Face-Detection:model.pt'
    yolov8_animeface = 'Fuyucchi/yolov8_animeface:yolov8x6_animeface.pt'


@dataclass
class YoloSettings:
    models_to_install = [YoloModels.yolov8_face, YoloModels.yolov8_animeface]

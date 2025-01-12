from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import YoloModel

@dataclass
class YoloSettings:
    connection = ConnectionSettings(20302)
    models_to_downloads = (
        YoloModel('arnabdhar/YOLOv8-Face-Detection', 'model.pt'), #Photorealistic faces
        YoloModel('Fuyucchi/yolov8_animeface', 'yolov8x6_animeface.pt') #Anime faces
    )
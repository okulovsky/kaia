from pydantic import BaseModel
from typing import Dict, List, Any

class CoordsFaceSquare(BaseModel):
    objects: List[Dict]

class ImageFormat(BaseModel):
    image_base64: str

class LoadModelRequest(BaseModel):
    model_id: str

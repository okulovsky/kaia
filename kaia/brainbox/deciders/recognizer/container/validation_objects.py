from pydantic import BaseModel
from typing import Dict, List, Any

class CoordsFaceSquare(BaseModel):
    faces_coords: Dict[str, Dict[str, int]]

class ImageFormat(BaseModel):
    image_base64: str

class LoadModelRequest(BaseModel):
    repo_id: str
    model_filename: str
import os
from typing import List, Dict, Any, Tuple

import numpy as np
import cv2
from insightface.app import FaceAnalysis


class FaceEmbedder:
    def __init__(
        self,
        model_name: str = "buffalo_l",
        det_size: Tuple[int, int] = (320, 320),
    ):
        """
        Keep a single InsightFace FaceAnalysis instance.
        Always try CUDA first, then fallback to CPU.
        """
        self.model_name = model_name
        self.det_size = det_size
        self.providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        self.app = FaceAnalysis(name=self.model_name, providers=self.providers)
        self.app.prepare(ctx_id=0, det_size=self.det_size)

    def extract_embeddings(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Decode image bytes, detect faces, and return for each face:
          { "bbox": [x1, y1, x2, y2], "embedding": [float, ...] }
        bbox coordinates are rounded to integers.
        """
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image from bytes.")

        faces = self.app.get(img)

        results: List[Dict[str, Any]] = []
        for f in faces:
            bbox_xyxy = [
                int(round(f.bbox[0])),
                int(round(f.bbox[1])),
                int(round(f.bbox[2])),
                int(round(f.bbox[3])),
            ]
            emb = f.normed_embedding.astype(float).tolist()  # 512 floats
            results.append({"bbox": bbox_xyxy, "embedding": emb})

        return results
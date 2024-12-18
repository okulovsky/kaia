import base64
from io import BytesIO

import cv2
from loguru import logger

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

import numpy as np

from cv2 import cvtColor, COLOR_BGR2GRAY, Laplacian, CV_64F
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from numpy.typing import NDArray


class VideoProcessorApp:
    router = APIRouter()

    def __init__(self):
        self._similarity_threshold = 0.9
        self._blur_threshold = 150
        self.data_directory = "/data"
        self.processed_frames = []

        self.start_index_batch = 0

    def create_app(self):
        app = FastAPI()
        VideoProcessorApp.router.add_api_route("/", self.index, methods=["GET"])
        VideoProcessorApp.router.add_api_route("/processing_video", self.processing_video, methods=["POST"])
        VideoProcessorApp.router.add_api_route("/get_processed_frames", self.get_processed_frames, methods=["GET"])
        app.include_router(VideoProcessorApp.router)

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    def processing_video(self, file_name: str):
        logger.info("Другой образ не?")
        local_path_to_video = f"./{self.data_directory}/{file_name}"
        cap = cv2.VideoCapture(local_path_to_video)

        last_image_for_comparison = None
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if last_image_for_comparison is None:
                last_image_for_comparison = frame
            else:
                cosine_similarity = self._get_cosine_similarity(last_image_for_comparison, frame)
                if cosine_similarity >= self._similarity_threshold:
                    continue
                last_image_for_comparison = frame

            if self._is_blurred_image(frame):
                continue

            self.processed_frames.append(frame)

            if len(self.processed_frames) == 3:
                break

        logger.info(len(self.processed_frames))

        cap.release()

        return "OK"

    def get_processed_frames(self, batch_size: int = 100):
        if not self.processed_frames:
            return JSONResponse(content={"status": "No frames to send"}, status_code=400)

        batch = self.processed_frames[self.start_index_batch: self.start_index_batch + batch_size]

        if batch:
            batch_base64 = []
            for frame in batch:
                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                buffer = BytesIO()
                pil_image.save(buffer, format="PNG")
                encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
                batch_base64.append(encoded_image)
            self.start_index_batch += batch_size
            return {"frames": batch_base64}

        self.start_index_batch = 0
        self.processed_frames.clear()
        return JSONResponse(content={"status": "All frames sent"})

    def _get_cosine_similarity(self, first_frame: NDArray[np.int32], second_frame: NDArray[np.int32]):
        gray_last_image_for_comparison = cvtColor(first_frame, COLOR_BGR2GRAY)
        gray_other_image = cvtColor(second_frame, COLOR_BGR2GRAY)
        gray_last_image_for_comparison = Image.fromarray(gray_last_image_for_comparison)
        gray_other_image = Image.fromarray(gray_other_image)

        comparator = self._get_comparator()

        first_embedding = comparator.encode(gray_last_image_for_comparison, convert_to_tensor=True)
        second_embedding = comparator.encode(gray_other_image, convert_to_tensor=True)

        return util.cos_sim(first_embedding, second_embedding)

    def _get_comparator(self):
        comparator = SentenceTransformer('clip-ViT-B-32')
        return comparator

    def _is_blurred_image(self, image: NDArray[np.int32]):
        is_blur, var = self._is_blurry(image, self._blur_threshold)
        if is_blur:
            return True
        return False

    def _is_blurry(self, image: NDArray[np.int32], threshold: int = 100):
        laplacian_var = Laplacian(image, CV_64F).var()
        return laplacian_var < threshold, laplacian_var
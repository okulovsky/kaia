import base64
import io

from huggingface_hub import hf_hub_download
from loguru import logger

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from ultralytics import YOLO

from validation_objects import LoadModelRequest, ImageFormat
from validation_objects import CoordsFaceSquare

import numpy as np

from cv2 import cvtColor, COLOR_BGR2GRAY
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from numpy.typing import NDArray


class FacesRecognizerApp:
    router = APIRouter()

    def __init__(self):
        self._similarity_threshold = 0.9
        self.model = None
        self.model_name = None
        self.data_directory = "/data" # Path(__file__).parent / "data"
        self.name_image_png = "image.png"

    def create_app(self):
        app = FastAPI()
        FacesRecognizerApp.router.add_api_route("/", self.index, methods=["GET"])
        FacesRecognizerApp.router.add_api_route("/from_image", self.get_coordinates_anime_faces_square_from_image,
                                                methods=["GET"])
        FacesRecognizerApp.router.add_api_route("/from_video", self.get_coordinates_anime_faces_square_from_video,
                                                methods=["GET"])
        FacesRecognizerApp.router.add_api_route("/load_model", self.load_model, methods=["POST"])
        FacesRecognizerApp.router.add_api_route("/get_loaded_model", self.get_loaded_model, methods=["GET"])
        app.include_router(FacesRecognizerApp.router)

        # использовать для встречи
        # self._load_model_internal("Fuyucchi/yolov8_animeface", "yolov8x6_animeface.pt")

        return app

    def index(self):
        return f"{type(self).__name__} is running"

    def _load_model_internal(self, repo_id: str, model_filename: str):
        # модель для распознавания лиц реальных людей: repo_id="arnabdhar/YOLOv8-Face-Detection", filename="model.pt"
        # модель для распознавания аниме-лиц: repo_id="Fuyucchi/yolov8_animeface"", filename="yolov8x6_animeface.pt"
        try:
            path_to_cache_model = hf_hub_download(repo_id=repo_id, filename=model_filename, cache_dir=self.data_directory)
        except:
            raise Exception("The model could not be loaded. Please check the correctness of the input data.")
        self.model = YOLO(path_to_cache_model)
        # self.model.to("cuda")
        # self.model_name = filename.split(".")[0]
        return "OK"

    async def load_model(self, request: LoadModelRequest):
        repo_id, model_filename = request.repo_id, request.model_filename
        return self._load_model_internal(repo_id, model_filename)

    def get_loaded_model(self):
        return JSONResponse(content={"name": self.model_name})

    async def get_coordinates_anime_faces_square_from_image(self, request: ImageFormat) -> CoordsFaceSquare:
        raw_img = await self._extract_image_from_requests_body(request)
        self._save_img_base64_to_png(raw_img)
        source = f"{self.data_directory}/{self.name_image_png}"
        results = self.model(source, stream=False)
        faces_coords = self._format_result(results)

        return {"faces_coords": faces_coords}

    async def get_coordinates_anime_faces_square_from_video(self, video_name: str) -> CoordsFaceSquare:
        source = f"{self.data_directory}/{video_name}"
        results = self.model(source, stream=True)
        faces_coords = self._format_result(results)
        faces_coords = self.drop_similarity_img(results, faces_coords)

        return {"faces_coords": faces_coords}

    def _format_result(self, results) -> CoordsFaceSquare:
        faces_coords = dict()
        num_face = 0
        for result in results:
            result_faces_coords = dict()
            for box in result.boxes.xywh:
                x_center, y_center, w, h = round(box[0].item()), round(box[1].item()), round(box[2].item()), round(box[3].item())
                result_faces_coords[f"face_{num_face}"] = {
                    "x_center": x_center,
                    "y_center": y_center,
                    "w": w,
                    "h": h,
                }
                num_face += 1
            faces_coords.update(result_faces_coords)

        return faces_coords

    async def _extract_image_from_requests_body(self, request: ImageFormat):
        str_image_base64 = request.image_base64
        raw_img = str_image_base64.replace("data:image/jpeg;base64,", "").strip()

        return raw_img

    def _save_img_base64_to_png(self, img_base64: str):
        bytes_img = base64.b64decode(img_base64.replace("data:image/jpeg;base64,", "").strip())
        bytes_io = io.BytesIO(bytes_img)
        bytes_io.seek(0)
        img = Image.open(bytes_io)
        img.save(f"{self.data_directory}/{self.name_image_png}", "PNG")

    def drop_similarity_img(self, results, faces_coords: CoordsFaceSquare) -> CoordsFaceSquare:
        last_image_for_comparison = None
        last_face_coords = None
        images_without_similarity = {}

        for result, (name, face_coords) in zip(results, faces_coords.items()):
            if last_image_for_comparison is None:
                last_image_for_comparison = result.orig_img
                last_face_coords = face_coords
            else:
                current_img = result.orig_img
                cosine_similarity = self._get_cosine_similarity(last_image_for_comparison, current_img)
                if cosine_similarity >= self._similarity_threshold:
                    continue
                last_image_for_comparison = current_img
                last_face_coords = face_coords
            images_without_similarity[name] = last_face_coords

        return images_without_similarity

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


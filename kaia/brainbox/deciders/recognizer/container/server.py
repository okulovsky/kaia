import base64
import io

from huggingface_hub import hf_hub_download
from loguru import logger

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from ultralytics import YOLO

from validation_objects import LoadModelRequest
from validation_objects import CoordsFaceSquare
from PIL import Image


class RecognizerApp:
    router = APIRouter()

    def __init__(self):
        self._similarity_threshold = 0.9
        self.model = None
        self.model_name = None
        self.data_directory = "/data"
        self.name_image_png = "image.png"

    def create_app(self):
        app = FastAPI()
        RecognizerApp.router.add_api_route("/", self.index, methods=["GET"])
        RecognizerApp.router.add_api_route("/post_image", self.post_image, methods=["POST"])
        RecognizerApp.router.add_api_route("/get_coordinates_faces", self.get_coordinates_faces, methods=["GET"])
        RecognizerApp.router.add_api_route("/load_model", self.load_model, methods=["POST"])
        RecognizerApp.router.add_api_route("/get_loaded_model", self.get_loaded_model, methods=["GET"])
        app.include_router(RecognizerApp.router)

        self._load_model_internal("Fuyucchi/yolov8_animeface", "yolov8x6_animeface.pt")

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

    async def post_image(self, request: Request):
        await self._save_img_base64_to_png(request)

        return "OK"

    def get_coordinates_faces(self) -> CoordsFaceSquare:
        source = f"{self.data_directory}/{self.name_image_png}"
        results = self.model(source, stream=False)
        faces_coords = self._format_result(results)

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

    async def _save_img_base64_to_png(self, request: Request):
        form = await request.form()
        img_base64 = form["image_base64"]
        bytes_img = base64.b64decode(img_base64.replace("data:image/jpeg;base64,", "").strip())
        bytes_io = io.BytesIO(bytes_img)
        bytes_io.seek(0)
        img = Image.open(bytes_io)
        img.save(f"{self.data_directory}/{self.name_image_png}", "PNG")
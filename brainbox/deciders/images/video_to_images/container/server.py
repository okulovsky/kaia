import base64
import os
import shutil
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
from model import get_comparator


class VideoProcessorApp:


    def __init__(self):
        self._similarity_threshold = 0.9
        self._blur_threshold = 150
        self.processed_frames = []
        self.start_index_batch = 0
        self.input_directory = '/resources/input'
        self.output_directory = '/resources/output'


    def run(self, file_name: str):
        self.comparator = get_comparator()
        self.processing_video(file_name)


    def processing_video(self, file_name: str):
        local_path_to_video = f"{self.input_directory}/{file_name}"
        print(f"File {local_path_to_video} is found: {os.path.isfile(local_path_to_video)}")

        shutil.rmtree(self.output_directory, ignore_errors=True)
        os.makedirs(self.output_directory)

        cap = cv2.VideoCapture(local_path_to_video)

        last_image_for_comparison = None
        print("Starting cap")
        cap_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print('Not ret')
                break
            print(f"Cap count {cap_count}")
            cap_count+=1

            if last_image_for_comparison is None:
                last_image_for_comparison = frame
            else:
                cosine_similarity = self._get_cosine_similarity(last_image_for_comparison, frame)
                if cosine_similarity >= self._similarity_threshold:
                    continue
                last_image_for_comparison = frame

            if self._is_blurred_image(frame):
                continue

            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            pil_image.save(os.path.join(self.output_directory, f'{cap_count}.png'), format="PNG")

        cap.release()

        return "OK"




    def _get_cosine_similarity(self, first_frame: NDArray[np.int32], second_frame: NDArray[np.int32]):
        gray_last_image_for_comparison = cvtColor(first_frame, COLOR_BGR2GRAY)
        gray_other_image = cvtColor(second_frame, COLOR_BGR2GRAY)
        gray_last_image_for_comparison = Image.fromarray(gray_last_image_for_comparison)
        gray_other_image = Image.fromarray(gray_other_image)

        comparator = self.comparator

        first_embedding = comparator.encode(gray_last_image_for_comparison, convert_to_tensor=True)
        second_embedding = comparator.encode(gray_other_image, convert_to_tensor=True)

        return util.cos_sim(first_embedding, second_embedding)



    def _is_blurred_image(self, image: NDArray[np.int32]):
        is_blur, var = self._is_blurry(image, self._blur_threshold)
        if is_blur:
            return True
        return False

    def _is_blurry(self, image: NDArray[np.int32], threshold: int = 100):
        laplacian_var = Laplacian(image, CV_64F).var()
        return laplacian_var < threshold, laplacian_var
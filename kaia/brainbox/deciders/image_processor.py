import base64

import numpy as np
from numpy.typing import NDArray

from kaia.brainbox import IDecider
from collections import namedtuple
from cv2 import Laplacian, CV_64F

from kaia.brainbox.deciders.faces_recognizer.container.validation_objects import CoordsFaceSquare, ImageFormat

Rectangle = namedtuple("Rectangle", ["X", "Y", "W", "H"])

class ImageProcessor(IDecider):
    def __init__(self):
        self._image = None
        self._blur_threshold = 150

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def set_image(self, image_base64: str):
        raw_img = image_base64.replace("data:image/jpeg;base64,", "").strip()
        self._image = self._deserialize_img(raw_img)

    def get_max_squares(self, faces_coords: CoordsFaceSquare) -> CoordsFaceSquare:
        max_squares_coords = dict()
        face_count = 0
        for name, face_coords in faces_coords:
            orig_img_h, orig_img_w, _ = self._image.shape
            x_center, y_center, w, h = face_coords["x_center"], face_coords["y_center"], face_coords["w"], face_coords["h"]
            x, y = x_center - w // 2, y_center - h // 2

            x_copy, y_copy, w_copy, h_copy = self._to_square(x, y, w, h)

            while True:
                expanded_x = max(0, x_copy - 1)
                expanded_y = max(0, y_copy - 1)
                expanded_w = w_copy + 5
                expanded_h = h_copy + 5

                if expanded_x + expanded_w >= orig_img_w:
                    expanded_w = orig_img_w - expanded_x
                    expanded_h = expanded_w
                if expanded_y + expanded_h >= orig_img_h:
                    expanded_h = orig_img_h - expanded_y
                    expanded_w = expanded_h

                expanded_rect = Rectangle(expanded_x, expanded_y, expanded_w, expanded_h)

                intersecting = False
                for other_box in face_coords:
                    other_x_center, other_y_center, other_w, other_h = other_box["x"], other_box["y"], other_box["w"], other_box["h"]
                    other_x, other_y = other_x_center - other_w // 2, other_y_center - other_h // 2
                    if (other_x, other_y, other_w, other_h) == (x, y, w, h):
                        continue
                    other_rect = Rectangle(other_x, other_y, other_w, other_h)
                    if self._check_intersection(expanded_rect, other_rect):
                        intersecting = True
                        break

                if intersecting or (expanded_y == 0 and expanded_y + expanded_h == orig_img_h) or \
                        (expanded_x == 0 and expanded_x + expanded_w == orig_img_w):
                    break

                x_copy, y_copy, w_copy, h_copy = expanded_x, expanded_y, expanded_w, expanded_h
                max_squares_coords[f"face{face_count}"].update({
                    "x": x_copy,
                    "y": y_copy,
                    "w": w_copy,
                    "h": h_copy,
                })
                face_count += 1

        return {"faces_coords": max_squares_coords}

    def _to_square(self, x: int, y:int, w: int, h: int):
        if h > w:
            h = w
        else:
            w = h

        return Rectangle(x, y, w, h)

    def get_crop_image(self, image: NDArray[np.int32], rectangle: Rectangle):
        cropped_image = image[rectangle.Y: rectangle.Y + rectangle.H, rectangle.X: rectangle.X + rectangle.W]
        return cropped_image

    async def drop_blurred_images(self, faces_coords: CoordsFaceSquare) -> CoordsFaceSquare:
        not_blurred_images = {}
        for name, face_coords in faces_coords:
            rect = Rectangle(face_coords["x"], face_coords["y"], face_coords["w"], face_coords["h"])
            if self._is_blurred_image(self.get_crop_image(self._image, rect)):
                continue
            not_blurred_images[name] = face_coords

        return {"faces_coords": not_blurred_images}

    def _is_blurred_image(self, image: NDArray[np.int32]):
        is_blur, var = self._is_blurry(image, self._blur_threshold)
        if is_blur:
            return True
        return False

    def _is_blurry(self, image: NDArray[np.int32], threshold: int = 100):
        laplacian_var = Laplacian(image, CV_64F).var()
        return laplacian_var < threshold, laplacian_var

    def _check_intersection(self, rect1: Rectangle, rect2: Rectangle):
        x, y, w, h = rect1
        other_x, other_y, other_w, other_h = rect2
        if x > other_x + other_w or x + w < other_x or y > other_y + other_h or y + h < other_y:
            return False
        return True

    def _deserialize_img(self, image_base64: str):
        array_bytes = base64.b64decode(image_base64)
        deserialize_img = np.frombuffer(array_bytes, np.int32)

        return deserialize_img
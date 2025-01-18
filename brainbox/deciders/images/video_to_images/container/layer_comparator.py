from typing import Iterable
from cv2 import cvtColor, COLOR_BGR2GRAY, Laplacian, CV_64F
from PIL import Image
from sentence_transformers import SentenceTransformer, util
from frame import Frame

def get_comparator():
    comparator = SentenceTransformer('clip-ViT-B-32')
    return comparator


def layer_comparator(iterable: Iterable[Frame]):
    old_embedding = None
    cmp = get_comparator()

    for frame in iterable:
        gray_image = cvtColor(frame.frame, COLOR_BGR2GRAY)
        gray_image = Image.fromarray(gray_image)
        embedding = cmp.encode(gray_image, convert_to_tensor=True)

        if old_embedding is not None:
            frame.comparator_delta = util.cos_sim(embedding, old_embedding).item()

        old_embedding = embedding
        yield frame

from sentence_transformers import SentenceTransformer, util

def get_comparator():
    comparator = SentenceTransformer('clip-ViT-B-32')
    return comparator
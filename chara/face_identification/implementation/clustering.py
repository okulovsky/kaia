from dataclasses import dataclass
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
from matplotlib import pyplot as plt
from yo_fluq import *
from .assignment import Assignment
from avatar.server import AvatarApi

class Clustering:
    def __init__(self,
                 avatar_api: AvatarApi,
                 names: tuple[str, ...],
                 vectors: tuple[list[float], ...],
                 ):
        self.avatar_api = avatar_api
        self.names = names
        self.vectors = vectors
        self.Z = self._build_dendrogram_by_dot()



    def _build_dendrogram_by_dot(self, method: str = "average"):
        embeddings = self.vectors

        embs = np.asarray(embeddings, dtype=np.float32)

        # Normalize vectors (so dot product == cosine similarity)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.clip(norms, 1e-8, None)

        # Similarity matrix (dot product between all pairs)
        sim_matrix = np.dot(embs, embs.T)

        # Convert to distance matrix: distance = 1 - similarity
        dist_matrix = 1.0 - sim_matrix

        # Condensed form for linkage
        condensed = squareform(dist_matrix, checks=False)

        # Hierarchical clustering
        return linkage(condensed, method=method)


    def plot_dendrogram(self, height=None):
        plt.figure(figsize=(8, 4))
        dendrogram(
            self.Z,
            leaf_rotation=90,
            color_threshold=height,
        )
        plt.tight_layout()
        plt.show()


    def create_assignment(self, height):
        assignment = list(fcluster(self.Z, t=height, criterion="distance"))
        df = (
            Query
            .en(zip(self.names, assignment))
            .select(lambda z: dict(name=z[0], cluster=z[1]))
            .to_dataframe()
        )
        return Assignment(self.avatar_api, df)


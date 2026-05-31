from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from .dataset import IntentUtterance


class IntentStore:
    def __init__(
        self,
        persist_path: Path,
        model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        collection_name: str = 'intents',
    ):
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.embedding_fn = SentenceTransformerEmbeddingFunction(model_name=model_name)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={'hnsw:space': 'cosine'},
        )

    def load(self, utterances: list[IntentUtterance]):
        """Clears collection and loads all utterances with intent metadata."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={'hnsw:space': 'cosine'},
        )
        self.collection.add(
            ids=[str(i) for i in range(len(utterances))],
            documents=[u.text for u in utterances],
            metadatas=[{'intent': u.intent, 'language': u.language} for u in utterances],
        )

    def query(self, text: str, k: int = 5) -> list[dict]:
        """Returns k nearest neighbors: [{text, intent, distance}]."""
        results = self.collection.query(query_texts=[text], n_results=k)
        neighbors = []
        for i in range(len(results['documents'][0])):
            neighbors.append({
                'text': results['documents'][0][i],
                'intent': results['metadatas'][0][i]['intent'],
                'distance': results['distances'][0][i],
            })
        return neighbors

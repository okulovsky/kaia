import chromadb
try:
    from interface import IChroma
    from model import MODEL_NAME
except ImportError:
    from brainbox.deciders.utils.chroma.app.interface import IChroma
    from brainbox.deciders.utils.chroma.app.model import MODEL_NAME


class ChromaService(IChroma):
    def __init__(self, chroma_path: str = '/chroma', model_cache: str = '/home/app/fastembed_cache'):
        from fastembed import TextEmbedding
        self._embed_model = TextEmbedding(MODEL_NAME, cache_dir=model_cache)
        self.client = chromadb.PersistentClient(path=chroma_path)
        self._collection_name = 'intents'
        self.collection = self.client.get_or_create_collection(
            self._collection_name,
            metadata={'hnsw:space': 'cosine'},
        )

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._embed_model.embed(texts)]

    def train(self, utterances: list[dict]) -> None:
        try:
            self.client.delete_collection(self._collection_name)
        except Exception:
            pass
        self.collection = self.client.create_collection(
            self._collection_name,
            metadata={'hnsw:space': 'cosine'},
        )
        if not utterances:
            return
        texts = [u['text'] for u in utterances]
        embeddings = self._encode(texts)
        self.collection.add(
            ids=[str(i) for i in range(len(utterances))],
            embeddings=embeddings,
            documents=texts,
            metadatas=[{'intent': u.get('intent', ''), 'language': u.get('language', '')} for u in utterances],
        )

    def find_neighbors(self, text: str, k: int = 5) -> list[dict]:
        embedding = self._encode([text])
        results = self.collection.query(query_embeddings=embedding, n_results=k)
        return [
            {
                'text': results['documents'][0][i],
                'intent': results['metadatas'][0][i]['intent'],
                'distance': results['distances'][0][i],
            }
            for i in range(len(results['documents'][0]))
        ]

    def get_vector(self, text: str) -> list[float]:
        return self._encode([text])[0]

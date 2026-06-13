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
        self._loaded_collection_name: str|None = None
        self._loaded_collection = None

    def _get_collection_name(self, collection_name: str|None) -> str:
        if collection_name is None:
            return 'default'
        return collection_name

    def _get_collection(self, collection_name: str|None):
        collection_name = self._get_collection_name(collection_name)
        if self._loaded_collection is None or self._loaded_collection_name is None or self._loaded_collection_name !=collection_name:
            self._loaded_collection_name = collection_name
            self._loaded_collection = self.client.get_or_create_collection(
                collection_name,
                metadata={'hnsw:space': 'cosine'},
            )
        return self._loaded_collection

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._embed_model.embed(texts)]

    def train(self, utterances: list[dict], collection_name: str|None = None) -> None:
        try:
            self.client.delete_collection(self._get_collection_name(collection_name))
        except Exception:
            pass
        collection = self.client.create_collection(
            self._get_collection_name(collection_name),
            metadata={'hnsw:space': 'cosine'},
        )
        if not utterances:
            return
        texts = [u['text'] for u in utterances]
        embeddings = self._encode(texts)
        metadatas = [{'intent': u.get('intent', ''), 'language': u.get('language', '')} for u in utterances]
        chunk_size = 5000
        for start in range(0, len(utterances), chunk_size):
            end = start + chunk_size
            collection.add(
                ids=[str(i) for i in range(start, min(end, len(utterances)))],
                embeddings=embeddings[start:end],
                documents=texts[start:end],
                metadatas=metadatas[start:end],
            )

    def find_neighbors(self, text: str, k: int = 5, collection_name: str|None = None) -> list[dict]:
        embedding = self._encode([text])
        collection = self._get_collection(collection_name)
        results = collection.query(query_embeddings=embedding, n_results=k)
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

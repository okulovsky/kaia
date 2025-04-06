from fastapi import APIRouter, FastAPI
from langchain_chroma import Chroma
import torch
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4
import os
import shutil
from typing import List, Dict


class Retriever:
    router = APIRouter()

    def __init__(
            self,
            collection_name: str = "posts",
            embedding_model_name: str = "intfloat/multilingual-e5-large",
            persist_directory_name: str = "./posts_db"
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        self.persist_directory_name = persist_directory_name

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={
                "device": self.device,
            },
            cache_folder="/models",
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=50,
        )

        self._build_db()

    def create_app(self) -> FastAPI:
        app = FastAPI()
        Retriever.router.add_api_route("/", self.index, methods=["GET"])
        Retriever.router.add_api_route("/add_relevant_context", self.search_relevant_context, methods=["GET"])
        Retriever.router.add_api_route("/add_documents", self.add_documents, methods=["POST"])
        Retriever.router.add_api_route("/delete_documents", self.delete_documents, methods=["POST"])

        return app

    def index(self) -> str:
        return f"{type(self).__name__} is running"

    def search_relevant_context(self, query: str, n_samples: int = 5):
        documents = self.client.similarity_search(
            query,
            k=n_samples,
        )
        results = []
        for document in documents:
            result = dict(
                metadata=document.metadata,
                text=document.page_content,
            )
            results.append(result)

        return results



    def add_documents(self, data: List[Dict]):
        self._add_data_to_db(data)

    def delete_documents(self, ids: List[uuid4]):
        self.client.delete(ids=ids)

    def _build_db(self):
        if os.path.exists(f"{self.persist_directory_name}.zip"):
            shutil.unpack_archive(f"{self.persist_directory_name}.zip", self.persist_directory_name)
            self.client = self._init_chroma_client()

        elif os.path.exists(f"./datasets/data_for_db.json"):
            with open('./datasets/data_for_db.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            self.client = self._init_chroma_client()
            self._add_data_to_db(data)

        else:
            self.client = self._init_chroma_client()

    def _add_data_to_db(self, data: List[Dict]):
        docs = []
        ids = []
        for post in data:
            chunks = self.splitter.split_text(post["text"])
            for chunk in chunks:
                document = Document(
                    page_content=chunk,
                    metadata={
                        "source": post["source"],
                        "file": post["file"],
                    }
                )
                docs.append(document)
                ids.append(str(uuid4()))

        self.client.add_documents(documents=docs, ids=ids)

    def _init_chroma_client(self):
        return Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory_name,
            )
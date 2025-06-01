from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Form
from langchain_chroma import Chroma
import torch
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4
import shutil
from typing import List, Dict, Any


class Retriever:
    router = APIRouter()

    def __init__(self):
        self.persist_directory_name = Path(__file__).parent / "posts_db"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model = None
        self.client = None

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=50,
        )

    def create_app(self) -> FastAPI:
        app = FastAPI()
        Retriever.router.add_api_route("/", self.index, methods=["GET"])
        Retriever.router.add_api_route("/download_model", self.download_model, methods=["POST"])
        Retriever.router.add_api_route("/build_db/from_json", self.build_db_from_json, methods=["POST"])
        Retriever.router.add_api_route("/build_db/from_zip_archive", self.build_db_from_zip_archive, methods=["POST"])
        Retriever.router.add_api_route("/init_chroma_client", self.init_chroma_client, methods=["POST"])
        Retriever.router.add_api_route("/get_relevant_context", self.get_relevant_context, methods=["GET"])
        Retriever.router.add_api_route("/add_documents", self.add_documents, methods=["POST"])
        Retriever.router.add_api_route("/delete_documents", self.delete_documents, methods=["POST"])
        app.include_router(Retriever.router)

        return app

    async def index(self) -> str:
        return f"{type(self).__name__} is running"

    async def download_model(self, embedding_model_name: str) -> str:
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs={
                "device": self.device,
            },
            cache_folder=str(Path(__file__).parent / "models"),
        )
        return "OK"

    async def build_db_from_json(self, filename: str, collection_name: str) -> str:
        try:
            with open(Path(__file__).parent / "datasets" / filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
            await self.init_chroma_client(collection_name)
            await self._add_data_to_db(data)
            return "OK"
        except Exception as e:
            HTTPException(status_code=500, detail=str(e))

    async def build_db_from_zip_archive(self, archive_name: str, collection_name: str) -> str:
        try:
            shutil.unpack_archive(Path(__file__).parent / archive_name, self.persist_directory_name)
            await self.init_chroma_client(collection_name)
            return "OK"
        except Exception as e:
            HTTPException(status_code=500, detail=str(e))

    async def get_relevant_context(self, query: str, n_samples: int = 5) -> List[Dict[Any, Any]]:
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

    async def add_documents(self, data: List[Dict]) -> str:
        await self._add_data_to_db(data)
        return "OK"

    async def delete_documents(self, ids: List[uuid4]) -> str:
        self.client.delete(ids=ids)
        return "OK"

    async def _add_data_to_db(self, data: List[Dict]):
        docs = []
        ids = []
        for post_data in data:
            text = post_data.pop("text")
            chunks = self.splitter.split_text(text)
            for chunk in chunks:
                document = Document(
                    page_content=chunk,
                    metadata=post_data
                )
                docs.append(document)
                ids.append(str(uuid4()))

        self.client.add_documents(documents=docs, ids=ids)

    async def init_chroma_client(self, collection_name: str) -> str:
        self.client = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_model,
                persist_directory=str(self.persist_directory_name),
            )
        return "OK"
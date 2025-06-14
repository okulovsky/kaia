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

    def __init__(
            self,
            embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            collection_name: str = "default_collection",
    ):
        self.persist_directory_name = "/resources/posts_db"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model = self.download_model(embedding_model)
        self.client = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory_name,
            )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
        )

        datasets_dir = Path(__file__).parent / "datasets"
        json_files = list(datasets_dir.glob("*.json"))
        zip_files = list(datasets_dir.glob("*.zip"))

        self._build_db(json_files, zip_files)

    def _build_db(self, json_files: List[str], zip_files: List[str]) -> None:
        try:
            if json_files:
                with open(json_files[0], 'r', encoding='utf-8') as file:
                    data = json.load(file)
                self._add_data_to_db(data)
                print(f"Загружен JSON: {json_files[0].name}")
            elif zip_files:
                shutil.unpack_archive(zip_files[0], self.persist_directory_name)
                print(f"Распакован архив: {zip_files[0].name}")
            else:
                print("Ни одного JSON-файла или ZIP-архива не найдено.")
        except Exception as e:
            print(f"Ошибка при загрузке базы данных: {e}")

    def create_app(self) -> FastAPI:
        app = FastAPI()
        Retriever.router.add_api_route("/", self.index, methods=["GET"])
        Retriever.router.add_api_route("/get_relevant_context", self.get_relevant_context, methods=["GET"])
        Retriever.router.add_api_route("/add_documents", self.add_documents, methods=["POST"])
        Retriever.router.add_api_route("/delete_documents", self.delete_documents, methods=["POST"])
        app.include_router(Retriever.router)

        return app

    async def index(self) -> str:
        return f"{type(self).__name__} is running"

    def download_model(self, embedding_model_name: str) -> str:
        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model_name,
                model_kwargs={
                    "device": self.device,
                },
                cache_folder="/resources/models"
            )
            return embedding_model
        except Exception as e:
            raise HTTPException(f"Не удалось загрузить модель: {e}")


    def get_relevant_context(self, query: str, n_samples: int = 5) -> List[Dict[Any, Any]]:
        try:
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
        except Exception as e:
            raise HTTPException(f"Возникла ошибка при поиске релевантных текстов: {e}")

    def add_documents(self, data: List[Dict]) -> str:
        try:
            self._add_data_to_db(data)
            return "OK"
        except Exception as e:
            raise HTTPException(f"Возникла ошибка при добавлении данных: {e}")

    def delete_documents(self, ids: List[uuid4]) -> str:
        try:
            self.client.delete(ids=ids)
            return "OK"
        except Exception as e:
            raise HTTPException(f"Возникла ошибка при удалении данных: {e}")

    def _add_data_to_db(self, data: List[Dict]):
        try:
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
        except Exception as e:
            raise HTTPException(f"Возникла ошибка при добавлении данных в Chroma: {e}")

from __future__ import annotations
from pathlib import Path
from typing import Optional, Union
import mimetypes
import requests
from ..common import ApiError
from uuid import uuid4

class FileCacheApi:
    TIMEOUT = 60  # seconds

    def __init__(self, base_url: str, prefix: str = '/file-cache', subfolder: str|None = None):
        self.base = base_url.rstrip("/") + "/" + prefix.strip("/")
        self.subfolder = subfolder.strip('/') if subfolder is not None else ''
        if self.subfolder!='':
            self.subfolder+='/'


    def _url_file(self, filepath: str) -> str:
        return f"{self.base}/file/{self.subfolder}{filepath.lstrip('/')}"

    def _url_dir(self, dirpath: str) -> str:
        return f"{self.base}/dir/{self.subfolder}{dirpath.lstrip('/')}"


    def upload(self, data: Union[bytes, str, Path], filepath: str|None = None) -> str:
        if filepath is None:
            if isinstance(data, (str, Path)):
                filepath = Path(data).name
            else:
                filepath = str(uuid4())

        url = self._url_file(filepath)
        ctype, _ = mimetypes.guess_type(filepath)
        headers = {"Content-Type": ctype or "application/octet-stream"}

        if isinstance(data, (str, Path)):
            with open(data, "rb") as f:
                resp = requests.put(url, data=f, headers=headers, timeout=self.TIMEOUT)
        else:
            resp = requests.put(url, data=data, headers=headers, timeout=self.TIMEOUT)

        ApiError.check(resp)
        return filepath

    def open(self, filepath: str) -> bytes:
        url = self._url_file(filepath)
        resp = requests.get(url, timeout=self.TIMEOUT)
        ApiError.check(resp)
        return resp.content

    def download(self, filepath: str, dest_path: Union[str, Path]) -> Path:
        url = self._url_file(filepath)
        p = Path(dest_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=self.TIMEOUT) as resp:
            ApiError.check(resp)
            with p.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return p

    def delete(self, filepath: str) -> dict:
        url = self._url_file(filepath)
        resp = requests.delete(url, timeout=self.TIMEOUT)
        return ApiError.check(resp).json()

    def is_file(self, filepath: str) -> bool:
        url = self._url_file(filepath)
        resp = requests.head(url, timeout=self.TIMEOUT)
        if resp.status_code == 404:
            return False
        elif resp.status_code == 200:
            return True
        else:
            ApiError.check(resp)

    def list(self, path: str = '/', *, prefix: Optional[str] = None, suffix: Optional[str] = None, recursive: bool = False) -> list[str]|None:
        url = self._url_dir(path)
        params = {}
        if prefix is not None:
            params["prefix"] = prefix
        if suffix is not None:
            params["suffix"] = suffix
        if recursive:
            params["recursive"] = "1"
        resp = requests.get(url, params=params, timeout=self.TIMEOUT)
        if resp.status_code == 404:
            return None
        return ApiError.check(resp).json()

    def is_folder(self, filepath: str) -> bool:
        url = self._url_dir(filepath)
        resp = requests.head(url, timeout=self.TIMEOUT)
        if resp.status_code == 404:
            return False
        elif resp.status_code == 200:
            return True
        else:
            ApiError.check(resp)
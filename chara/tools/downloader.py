from typing import *
from yo_fluq import Query, fluq
from bro.infra import FileIO
import requests
import time
import os

from pathlib import Path
import numpy as np


class DownloadEngine:
    def get(self, url):
        raise NotImplementedError()


class RequestsEngine(DownloadEngine):
    def __init__(self, cookies_for_domain=None, return_content_instead_of_text: bool = False):
        self.cookies_for_domain = cookies_for_domain
        self.return_content_instead_of_text = return_content_instead_of_text

    def get(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        if self.cookies_for_domain is not None:
            import browser_cookie3
            cookies = browser_cookie3.firefox(domain_name=self.cookies_for_domain)
        else:
            cookies = None
        response = requests.get(url, headers=headers, cookies=cookies)
        err = None
        if response.status_code != 200:
            err = response.status_code
        if self.return_content_instead_of_text:
            return response.content, err
        else:
            return response.text, err


class Downloader:
    def __init__(self, engine: Optional[RequestsEngine] = None):
        self.engine = RequestsEngine() if engine is None else engine

    def value_to_filename(self, value):
        return value.replace('/', '___')

    def download(
            self,
            url_pattern: str,
            folder: Path,
            values: List[str],
            pause_time: Union[float, Tuple[float, float]] = 1,
            dont_redownload: bool = True,
            with_progress_bar: bool = True,
            continue_if_not_found: bool = True,
            extension='.html',
            stop_if_filter=None
    ):
        folder = Path(folder)
        vs = Query.en(values).select(str)
        if with_progress_bar:
            vs = vs.feed(fluq.with_progress_bar())
        first_time = True
        for value in vs:
            fvalue = self.value_to_filename(value)
            path = folder / (fvalue + extension)
            os.makedirs(path.parent, exist_ok=True)
            if path.is_file():
                if dont_redownload:
                    continue
            url = url_pattern.format(value)
            if not first_time:
                if isinstance(pause_time, float) or isinstance(pause_time, int):
                    time.sleep(pause_time)
                else:
                    mx, mn = pause_time
                    t = np.random.rand() * (mx - mn) + mn
                    time.sleep(t)
            first_time = False
            text, err = self.engine.get(url)
            if err is not None:
                msg = f'Error when accessing {url}: status {err}'
                if not continue_if_not_found:
                    raise ValueError(msg)
                else:
                    print(msg)
                    continue
            if stop_if_filter is not None:
                if stop_if_filter(text):
                    break
            if isinstance(text, str):
                FileIO.write_text(text, path)
            elif isinstance(text,bytes):
                FileIO.write_bytes(text, path)
            else:
                raise ValueError(f"Unknown content type {type(text)}")
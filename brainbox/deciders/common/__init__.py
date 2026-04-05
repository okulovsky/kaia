import os
from unittest import TestCase
from ...framework import Loc, FileIO, LocalExecutor
from pathlib import Path



VOICEOVER_TEXT = 'The quick brown fox jumps over the lazy dog'


def download_file(url: str, file: Path, keep_current_if_exists: bool = True):
    import requests
    from tqdm import tqdm

    file = Path(file)
    if file.is_file():
        if keep_current_if_exists:
            return
        else:
            os.unlink(file)

    response = requests.head(url)
    file_size = int(response.headers.get('Content-Length', 0))  # Get the file size in bytes

    if file_size == 0:
        print("Unable to determine file size. Proceeding without progress bar.")

    # Make the GET request for the file content
    response = requests.get(url, stream=True)
    response.raise_for_status()

    os.makedirs(file.parent, exist_ok=True)

    # Write the file with a progress bar
    with open(file, 'wb') as file, tqdm(
            total=file_size,
            unit='B',
            unit_scale=True,
            desc=str(file)
    ) as progress_bar:
        for chunk in response.iter_content(chunk_size=8192):  # Read in 8 KB chunks
            file.write(chunk)
            progress_bar.update(len(chunk))



from huggingface_hub import HfApi, hf_hub_url
import requests

def check_hf_model_access(repo_id: str, token: str):
    api = HfApi()
    url = hf_hub_url(repo_id=repo_id, filename="config.json")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.head(url, headers=headers)
    if response.status_code == 403:
        raise ValueError(f"You do not have the access to {repo_id}. Visit https://huggingface.co/{repo_id} and request access")

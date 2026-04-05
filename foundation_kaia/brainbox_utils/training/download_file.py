from pathlib import Path
import os

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

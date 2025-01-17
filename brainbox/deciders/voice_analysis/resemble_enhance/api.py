from pathlib import Path
import requests
from kaia.brainbox.core import IApiDecider

class Denoiser(IApiDecider):
    def __init__(self, address: str):
        self.address = address

    def post_audio(self, path_to_file: Path | str):
        """
        Posts an audio file to the enhancement service.
        :param path_to_file: Path or string path to the audio file.
        :return: JSON response from the server.
        """
        with open(path_to_file, 'rb') as audio_file:
            files = {'files[]': audio_file}
            response = requests.post(f"http://{self.address}/enhance", files=files)

        if response.status_code != 200:
            raise ValueError(response.text)

        return response.json()

    def get_processed_files(self):
        """
        Retrieves the list of processed files from the enhancement service.
        :return: JSON response containing processed file details.
        """
        response = requests.get(f"http://{self.address}/processed_files")
        if response.status_code != 200:
            raise ValueError(response.text)

        return response.json()

    def download_file(self, filename: str, save_path: Path | str):
        """
        Downloads a processed file from the enhancement service.
        :param filename: Name of the file to download.
        :param save_path: Path to save the downloaded file.
        :return: None
        """
        response = requests.get(f"http://{self.address}/downloads/{filename}", stream=True)
        if response.status_code != 200:
            raise ValueError(response.text)

        # Save the file to the specified path
        with open(save_path, 'wb') as out_file:
            out_file.write(response.content)
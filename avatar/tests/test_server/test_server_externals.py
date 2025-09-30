from avatar.server import AvatarApi, AvatarServerSettings
from avatar.server.components import FileCacheComponent, StaticPathsComponent, MainComponent
from unittest import TestCase
import requests
from foundation_kaia.misc import Loc
from pathlib import Path

class AvatarServerExternals(TestCase):
    def test_upload_download(self):
        with Loc.create_test_folder() as cache_folder:
            settings = AvatarServerSettings((
                FileCacheComponent(cache_folder),
            ))
            with AvatarApi.Test(settings) as api:
                content=b'123456'
                api.file_cache.upload(content, 'test_file')
                self.assertTrue( (cache_folder/'test_file').is_file() )
                received_content = api.file_cache.open('test_file')
                self.assertEqual(content, received_content)

    def test_custom_index(self):
        text =  'text'
        settings = AvatarServerSettings((MainComponent(text),))
        with AvatarApi.Test(settings) as api:
            result = requests.get(f'http://{api.address}/main')
            result.raise_for_status()
            self.assertEqual(text, result.text)

    def test_static_folders(self):
        path = Path(__file__).parent/'files'
        settings = AvatarServerSettings((
            StaticPathsComponent(dict(f1=path/'static_1', f2=path/'static_2')),
        ))
        with AvatarApi.Test(settings) as api:
            result = requests.get(f'http://{api.address}/f1/file_1')
            result.raise_for_status()
            self.assertEqual('content 1', result.text)


            result = requests.get(f'http://{api.address}/f2/file_2')
            result.raise_for_status()
            self.assertEqual('content 2', result.text)

            result = requests.get(f'http://{api.address}/f2/subfolder/file_3')
            result.raise_for_status()
            self.assertEqual('content 3', result.text)






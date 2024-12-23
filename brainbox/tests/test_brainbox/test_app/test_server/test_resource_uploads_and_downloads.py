from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from brainbox.deciders import Boilerplate

class ResourcesUploadsAndDownloadsTestCase(TestCase):
    def test_resource_uploads_and_downloads(self):
        with BrainBoxApi.Test([Boilerplate()], False) as api:
            api.controller_api.install(Boilerplate)
            self.assertEqual(
                {'nested/resource': 'Boilerplate nested resource', 'resource': 'Boilerplate resource'},
                api.execute(BrainBoxTask.call(Boilerplate,'').resources())
            )
            api.controller_api.delete_resource(Boilerplate, 'nested/resource')
            self.assertEqual(
                {'resource': 'Boilerplate resource'},
                api.execute(BrainBoxTask.call(Boilerplate,'').resources())
            )
            api.controller_api.upload_resource(Boilerplate, 'new/file', b'Test')
            self.assertEqual(
                {'resource': 'Boilerplate resource', 'new/file': 'Test'},
                api.execute(BrainBoxTask.call(Boilerplate,'').resources())
            )



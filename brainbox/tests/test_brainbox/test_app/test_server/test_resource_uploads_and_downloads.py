from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from brainbox.deciders import HelloBrainBox

class ResourcesUploadsAndDownloadsTestCase(TestCase):
    def test_resource_uploads_and_downloads(self):
        with BrainBoxApi.Test([HelloBrainBox()], False) as api:
            api.controller_api.install(HelloBrainBox)
            self.assertEqual(
                {'nested/resource': 'HelloBrainBox nested resource', 'resource': 'HelloBrainBox resource'},
                api.execute(BrainBoxTask.call(HelloBrainBox,'').resources())
            )
            api.controller_api.delete_resource(HelloBrainBox, 'nested/resource')
            self.assertEqual(
                {'resource': 'HelloBrainBox resource'},
                api.execute(BrainBoxTask.call(HelloBrainBox,'').resources())
            )
            api.controller_api.upload_resource(HelloBrainBox, 'new/file', b'Test')
            self.assertEqual(
                {'resource': 'HelloBrainBox resource', 'new/file': 'Test'},
                api.execute(BrainBoxTask.call(HelloBrainBox,'').resources())
            )
            lst = api.controller_api.list_resources(HelloBrainBox,'/')
            self.assertEqual(['resource','new/file'], lst)


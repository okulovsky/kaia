from brainbox.framework import BrainBoxApi, ControllerApi, Loc, Locator
from brainbox.deciders import HelloBrainBox
from unittest import TestCase
import os
from yo_fluq import *
from pprint import pprint

class ResourcesTestCase(TestCase):
    def test_resources_uploads(self):
        with Loc.create_test_folder() as test_folder:
            with ControllerApi.Test([HelloBrainBox.Controller()], test_folder) as api:
                locator = Locator(test_folder)
                self.assertEqual(0, Query.folder(locator.resources_folder, '**/*').count())
                api.uninstall(HelloBrainBox, True)

                result = api.install(HelloBrainBox)
                self.assertIsNone(result.error)

                self.assertEqual(2, Query.folder(locator.resources_folder, '**/*').where(lambda z: z.is_file()).count())

                resources_list = api.list_resources(HelloBrainBox, '/')
                print(resources_list)
                self.assertEqual(2, len(resources_list))

                api.delete_resource(HelloBrainBox, 'nested')

                self.assertEqual(1, len(api.list_resources(HelloBrainBox,'/')))

                api.upload_resource(HelloBrainBox,'new/file', b'Hello')
                self.assertEqual(2, len(api.list_resources(HelloBrainBox, '/')))

                file = api.download_resource(HelloBrainBox,'new/file', test_folder/'created_file')
                self.assertEqual(b'Hello', FileIO.read_bytes(test_folder/'created_file'))






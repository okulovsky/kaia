from brainbox.framework import BrainBoxApi, ControllerApi, Loc, Locator
from brainbox.deciders import Boilerplate
from unittest import TestCase
import os
from yo_fluq import *
from pprint import pprint

class ResourcesTestCase(TestCase):
    def test_resources_uploads(self):
        with Loc.create_test_folder() as test_folder:
            with ControllerApi.Test([Boilerplate.Controller()], test_folder) as api:
                locator = Locator(test_folder)
                self.assertEqual(0, Query.folder(locator.resources_folder, '**/*').count())
                api.uninstall(Boilerplate, True)

                result = api.install(Boilerplate)
                self.assertIsNone(result.error)

                self.assertEqual(2, Query.folder(locator.resources_folder, '**/*').where(lambda z: z.is_file()).count())

                resources_list = api.list_resources(Boilerplate, '/')
                print(resources_list)
                self.assertEqual(2, len(resources_list))

                api.delete_resource(Boilerplate, 'nested')

                self.assertEqual(1, len(api.list_resources(Boilerplate,'/')))

                api.upload_resource(Boilerplate,'new/file', b'Hello')
                self.assertEqual(2, len(api.list_resources(Boilerplate, '/')))

                file = api.download_resource(Boilerplate,'new/file')
                self.assertEqual(b'Hello', file.content)






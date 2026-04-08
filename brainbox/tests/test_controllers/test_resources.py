from brainbox.framework import BrainBoxApi, Loc, Locator
from brainbox.deciders import HelloBrainBox
from unittest import TestCase
from yo_fluq import Query


class ResourcesTestCase(TestCase):
    def test_resources_uploads(self):
        with Loc.create_test_folder() as test_folder:
            with BrainBoxApi.test([HelloBrainBox.Controller()], locator=Locator(test_folder), run_controllers_in_default_environment=False) as api:
                locator = api.locator
                self.assertEqual(0, Query.folder(locator.resources_folder, '**/*').count())
                api.controllers.uninstall(HelloBrainBox, True)

                result = api.controllers.install(HelloBrainBox)
                self.assertIsNone(result.error)

                # After install: installation.yaml + models/google + models/duckduckgo
                self.assertEqual(3, Query.folder(locator.resources_folder, '**/*').where(lambda z: z.is_file()).count())

                resources_list = api.resources(HelloBrainBox).list('/', glob=True)
                print(resources_list)
                self.assertEqual(3, len(resources_list))

                api.resources(HelloBrainBox).upload('new/file', b'Hello')
                self.assertEqual(1, len(api.resources(HelloBrainBox).list_details('/new')))

                content = api.resources(HelloBrainBox).read('new/file')
                self.assertEqual(b'Hello', content)

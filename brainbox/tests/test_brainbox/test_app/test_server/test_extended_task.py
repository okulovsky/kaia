import os
from unittest import TestCase
from brainbox.framework import IDecider, FileIO, BrainBoxApi, BrainBoxTask, BrainBoxExtendedTask, CacheUploadPrerequisite, File

class Test(IDecider):
    def list(self):
        return {k:FileIO.read_text(self.cache_folder/k) for k in os.listdir(self.cache_folder)}




class ComplexPacksTestCase(TestCase):
    def test(self):
        with BrainBoxApi.Test([Test()]) as api:
            pack = BrainBoxExtendedTask(
                BrainBoxTask.call(Test).list(),
                prerequisite=CacheUploadPrerequisite(File('test1.txt',b'Test1'))
            )

            self.assertEqual({'test1.txt': 'Test1'}, api.execute(pack))


    

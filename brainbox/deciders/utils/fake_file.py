from ...framework import IDecider, File


class FakeFile(IDecider):
    def __call__(self, prefix:str = '', extension_with_dot='', array_length: int|None = None):
        if array_length is None:
            return File(self.current_job_id+'.output'+extension_with_dot, prefix)
        else:
            result = []
            for i in range(array_length):
                result.append(File(self.current_job_id+'.output.'+str(i)+extension_with_dot, prefix+str(i)))
            return result


from foundation_kaia.marshalling import service, JSON, FileLike
from foundation_kaia.brainbox_utils import brainbox_endpoint



@service
class IComfyUI:
    @brainbox_endpoint
    def workflow(self,
                 workflow: JSON,
                 input_0: FileLike|None = None,
                 input_1: FileLike|None = None,
                 input_2: FileLike|None = None,
                 input_3: FileLike|None = None,
                 input_4: FileLike|None = None,
                 ) -> FileLike:
        ...

from foundation_kaia.marshalling import service, JSON, FileLike
from foundation_kaia.brainbox_utils import brainbox_endpoint



@service
class IComfyUI:
    @staticmethod
    def input_placeholder(index: int) -> str:
        return f"<brainbox_input_placeholder_{index}>"

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

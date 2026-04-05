from ...deployment import LocalExecutor, Command
from ...common import Loc
from yo_fluq import FileIO

class GpuRegistry:
    _are_present = None

    @staticmethod
    def _get_fname():
        return Loc.temp_folder / 'gpus.json'

    @staticmethod
    def _from_file() -> bool:
        fname = GpuRegistry._get_fname()
        if not fname.is_file():
            return False
        try:
            data = FileIO.read_json(fname)
        except:
            return False

        if isinstance(data, dict) and 'has_gpus' in data:
            GpuRegistry._are_present = data['has_gpus']
            return True

        return False

    @staticmethod
    def _from_docker():
        try:
            LocalExecutor().execute(['docker', 'run', '--gpus', 'all', 'hello-world'],
                                    Command.Options(ignore_exit_code=False))
            GpuRegistry._are_present = True
        except:
            GpuRegistry._are_present = False

    @staticmethod
    def are_present():
        if GpuRegistry._are_present is None:
            if not GpuRegistry._from_file():
                GpuRegistry._from_docker()
                FileIO.write_json(dict(has_gpus=GpuRegistry._are_present), GpuRegistry._get_fname())
        return GpuRegistry._are_present
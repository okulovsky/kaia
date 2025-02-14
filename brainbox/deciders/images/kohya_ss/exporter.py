import copy


from ....framework import IPostprocessor, BrainBox, FileIO
from pathlib import Path

class LorasExporter(IPostprocessor):
    def __init__(self,
                 target_folder: Path,
                 only_last_version: bool = False,
                 cleanup: bool = True,
                 ):
        self.target_folder = Path(target_folder)
        self.only_last_version = only_last_version
        self.cleanup = cleanup

    def postprocess(self, result, api: BrainBox.Api):
        from .api import KohyaSS
        produced_files = api.controller_api.list_resources(KohyaSS, result['training_folder']+'/model')

        general_description = result['description']
        if general_description is None:
            general_description = {}

        for file in produced_files:
            name = file.split('/')[-1]
            prefix = result['training_id']
            suffix = '.safetensors'
            if not name.startswith(prefix):
                continue
            if not name.endswith(suffix):
                continue
            if self.only_last_version and name != prefix+suffix:
                continue
            api.controller_api.download_resource(KohyaSS, file, self.target_folder/name)
            description_filename = name+'.description.json'
            description = copy.deepcopy(general_description)
            description['interfix'] = name[len(prefix):-len(suffix)]
            description['model_filename'] = name
            FileIO.write_json(
                description,
                self.target_folder/description_filename
            )


        if self.cleanup:
            api.controller_api.delete_resource(KohyaSS, result['training_folder'], True)






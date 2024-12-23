from .template import TemplateWorkflow
from dataclasses import dataclass, field
from .....framework import FileLike, File

@dataclass
class WD14Interrogate(TemplateWorkflow):
    filename: FileLike.Type = field(metadata=TemplateWorkflow.meta('image','Load Image', is_input_file=True))
    threshold: float = 0.35
    character_threshold: float = 0.85
    model: str = field(default='wd-v1-4-moat-tagger-v2', metadata=TemplateWorkflow.meta(is_model_with_priority=0))
    output_filename: str = field(default='', metadata=TemplateWorkflow.meta('file', maps_to_job_id=True))


    def preprocess_value(self, field_name, value):
        if field_name=='output_filename':
            return value+'.txt'
        return value

    def postprocess(self, files: list[File]):
        if len(files)!=1:
            raise ValueError(f"Exactly 1 output file is expected for WD14, but was {len(files)}")
        if files[0].kind!=File.Kind.Text:
            raise ValueError(f"Text file is expected for WD14, but was {files[0].kind}")
        return files[0].string_content




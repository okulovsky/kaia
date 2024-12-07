from pathlib import Path
from zipfile import ZipFile
from .annotation_controller import AnnotationController

def export_images(
        root_path: Path,
        character_name_prefix: str|None = 'LoRA',
        replace_underscore_with_space: bool = True
):
    controller = AnnotationController(root_path)
    with ZipFile(root_path/'dataset.zip', 'w') as file:
        for annotation in controller.annotations:
            if annotation.stored.skipped:
                continue
            if not annotation.stored.reviewed:
                continue

            original_file_name = annotation.status.source_path.name.split('.')[0]
            file.write(
                annotation.status.upscaled_path,
                original_file_name+'.png'
            )

            tags = [tag.name for tag in annotation.stored.tags if tag.status]
            tags += annotation.stored.new_tags
            tags = [t for t in tags if t not in annotation.settings.exclude_tags]
            tags += annotation.settings.include_tags
            if character_name_prefix is not None:
                tags += [character_name_prefix+root_path.name]
            tags = list(set(tags))
            tags = ", ".join(tags)
            if replace_underscore_with_space:
                tags = tags.replace('_', ' ')
            file.writestr(
                original_file_name+'.txt',
                tags
            )
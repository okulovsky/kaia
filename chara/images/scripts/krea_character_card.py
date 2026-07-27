import copy
import io
import os
from typing import ClassVar

import yaml
from PIL import Image

from chara import Chara
from ..krea import KreaImageToImage
from pathlib import Path
from dataclasses import dataclass

SEED = 3281821941

@dataclass
class CharacterCardPrompt:
    common_prompt: str
    character_to_addition: dict[str, str]|None = None

    @staticmethod
    def read_from_yaml(path: Path) -> 'CharacterCardPrompt':
        with open(path) as f:
            data = yaml.safe_load(f)
        return CharacterCardPrompt(**data)


@dataclass
class CharacterCardGenerator:
    prompt: CharacterCardPrompt
    path: Path
    template: KreaImageToImage
    extension: str = 'png'
    source: str = 'source'

    Prompt: ClassVar = CharacterCardPrompt



    def create_prompt(self, name: str):
        result = self.prompt.common_prompt
        if self.prompt.character_to_addition is not None:
            result += "\n"+self.prompt.character_to_addition[name]
        return result

    def get_candidates(self):
        sample_folder = Chara.Apis.content_folder / f'images/character_cards/{self.source}'
        candidates = list(sample_folder.glob('*'))
        return candidates

    def upload_source(self, name: str):
        candidates = self.get_candidates()
        candidates = [c for c in candidates if c.name.startswith(name) and not c.name.endswith('txt')]
        if len(candidates) > 1:
            raise ValueError(f"More than one source for {name}: {candidates}")
        if len(candidates) == 0:
            raise ValueError(f"No source for {name}, source folder is {self.source}")
        filename = f'character_card_source_{name}.{self.extension}'
        Chara.Apis.brainbox_api.cache.upload(filename, candidates[0])
        return filename

    def generate_one(self, name: str, source_filename, delta: int = 0, size_modifier: float = 1):
        task = copy.deepcopy(self.template)
        task.source_image = source_filename
        task.prompt = self.create_prompt(name)
        task.width = int(task.width * size_modifier)
        task.height = int(task.height * size_modifier)
        task.seed = SEED + delta
        result = Chara.Apis.brainbox_api.execute(task)
        return Chara.Apis.brainbox_api.cache.read(result)

    def preview(self, *characters: str):
        preview_path = self.path / f'preview.{self.extension}'
        if preview_path.exists():
            os.unlink(preview_path)
        if len(characters) == 0:
            if self.prompt.character_to_addition is not None:
                characters = tuple(self.prompt.character_to_addition)
            else:
                candidates = self.get_candidates()
                candidates = [c for c in candidates if c.name.endswith(self.extension)]
                characters = tuple(c.name.replace(self.extension,'') for c in candidates)

        for name in characters:
            source_filename = self.upload_source(name)
            result = self.generate_one(name, source_filename, 0, 0.5)
            new_image = Image.open(io.BytesIO(result))
            new_image.load()
            if not preview_path.exists():
                new_image.save(preview_path)
            else:
                existing_image = Image.open(preview_path)
                existing_image.load()
                combined = Image.new(
                    'RGB',
                    (existing_image.width + new_image.width, max(existing_image.height, new_image.height)),
                    'white',
                )
                combined.paste(existing_image, (0, 0))
                combined.paste(new_image, (existing_image.width, 0))
                combined.save(preview_path)

    def generate(self, count: int, *characters: str):
        if len(characters) == 0:
            characters = tuple(self.prompt.character_to_addition)
        for name in characters:
            path = self.path/'generation'/name
            if path.exists():
                print(f"Generation exists for {name}, skipping")
                continue
            print(f"Starting for character {name}")
            os.makedirs(path)
            source_filename = self.upload_source(name)
            for i in range(count):
                result = self.generate_one(name, source_filename, i)
                with open(path/f'{i}.{self.extension}', 'wb') as f:
                    f.write(result)

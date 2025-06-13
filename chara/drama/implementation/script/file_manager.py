import json
import yaml
from brainbox.flow import JinjaPrompter
from pathlib import Path
from collections import OrderedDict
from yo_fluq import *
from ..scene import Message, Medium


class FileManager:
    def __init__(self, file, characters_file: Path|None = None):
        self.characters_file = characters_file
        self._parse_characters_file()
        self.file = file
        self._load_sections()

    def parse_yaml(self, section):
        return yaml.safe_load('\n'.join(section))


    def _parse_characters_file(self):
        from .character_script import CharacterScript
        if self.characters_file is not None:
            with open(self.characters_file, 'r') as cfile:
                characters = yaml.safe_load(cfile)
            self.predefined_characters = {k: CharacterScript.parse_one_character(v) for k, v in characters.items()}
        else:
            self.predefined_characters = {}

    def _load_sections(self):
        self.sections = OrderedDict()
        current_key = None
        for line in Query.file.text(self.file):
            if line.startswith('#'):
                current_key = line.replace('#', '').strip()
                if current_key not in self.sections:
                    self.sections[current_key] = []
            else:
                self.sections[current_key].append(line)

    def append_to_file(self, message: tuple[Message,...], covariates: dict|None):
        lines = []
        for key in self.sections:
            if key == 'Play':
                continue
            lines.append(f'# {key}')
            for line in self.sections[key]:
                lines.append(line)
        lines.append('# Play')
        for line in self.sections.get('Play', []):
            if line=='' or line.startswith('!'):
                continue
            lines.append(line)
            if line.startswith('{'):
                lines.append('')
        for m in message:
            lines.append(str(m))
        if covariates is not None:
            lines.append(json.dumps(covariates))
        lines.append('')
        with open(self.file, 'w') as file:
            file.write("\n".join(lines))





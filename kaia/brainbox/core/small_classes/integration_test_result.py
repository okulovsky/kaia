import json
from dataclasses import dataclass, field
from .file import File
from pathlib import Path
import os
from kaia.infra import FileIO
import traceback


@dataclass
class IntegrationTestResult:
    level: int = 0
    header: None|str = None
    content: None|str|File = None


    VOICEOVER_SAMPLE = 'The quick brown fox jumps over the lazy dog'

    @staticmethod
    def _render_one_item(content):
        from ipywidgets import Audio, Image, Label, HTML
        if isinstance(content, str):
            return Label(content)
        elif isinstance(content, File):
            if content.kind == File.Kind.Audio:
                return Audio(value=content.content, autoplay=False)
            elif content.kind == File.Kind.Image:
                return Image(value=content.content)
            elif content.kind == File.Kind.Json:
                s = json.dumps(json.loads(content.string_content), indent=4)
                return HTML(f"<pre>\n{s}</pre>")
            raise TypeError(f"Unknown file kind: {content.kind}")
        raise TypeError(f"Unknown content type {type(content)}")



    @staticmethod
    def _render_one_file(path):
        from ipywidgets import HTML, HBox

        result = []
        test = FileIO.read_pickle(path)
        test = list(test)
        for element in test:
            if not isinstance(element, IntegrationTestResult):
                raise TypeError(f"Wrong element of type {type(element)}")
            if element.header is not None:
                result.append(HTML(f'<h{element.level+2}>{element.header}</h{element.level+2}>'))
            if element.content is not None:
                result.append(HBox([IntegrationTestResult._render_one_item(element.content)]))

        return result


    @staticmethod
    def render_notebook_for_folder(path: Path):
        from ipywidgets import HTML, VBox
        files = list(sorted(os.listdir(path)))
        result = []
        for file in files:
            try:
                content = IntegrationTestResult._render_one_file(path/file)
            except:
                print(f"File {file}\n{traceback.format_exc()}")
                continue
            result.append(HTML(f'<h1>{file}</h1>'))
            result.extend(content)
        return VBox(result)


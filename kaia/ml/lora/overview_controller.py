from .status import Status, Folders, AnnotationSettings
import subprocess
import sys
from pathlib import Path
import os
from .image_tools import ConvertImage
from kaia.brainbox import BrainBoxApi, BrainBoxTask
from kaia.brainbox.deciders import Collector, CollectorTaskBuilder, Upscale
from kaia.ml.lora.brainbox_deciders.wd14_tagger import WD14Tagger
from kaia.infra import FileIO


class OverviewController:
    def __init__(self,
                 brainbox_api: BrainBoxApi,
                 root_folder,
                 preview_size: int = 100,
                 target_upscale_size: int = 1024,
                 upscale_model: str = '4x-AnimeSharp.pth',
                 interrogation_threshold: float = 0.05
                 ):
        self.brainbox_api = brainbox_api
        self.root_folder = root_folder
        self.preview_size = preview_size
        self.target_upscale_size = target_upscale_size
        self.upscale_model = upscale_model
        self.interrogation_threshold = interrogation_threshold

    def _make_crops(self):
        statuses = Status.gather_all(self.root_folder)
        for status in statuses:
            if status.cropped_path is not None:
                continue
            try:
                im = ConvertImage(status.source_path).to_pil()
                im = status.crop_rect.crop(im)
                path = status.build_cropped_path()
                os.makedirs(path.parent, exist_ok=True)
                im.save(path)
            except:
                pass

    def build_ai_pack(self):
        builder = CollectorTaskBuilder()
        builder.append(BrainBoxTask.call(WD14Tagger).tags(), dict(type='tags'))

        for status in Status.gather_all(self.root_folder):
            if status.cropped_path is None:
                continue

            upscale_dependency = None
            if status.upscaled_path is None:
                im = ConvertImage(status.cropped_path).to_pil()
                size = max(im.width, im.height)
                ratio = self.target_upscale_size/size
                if ratio<=1:
                    os.makedirs(status.build_upscaled_path().parent, exist_ok=True)
                    ConvertImage(im).resize_to_exact(self.target_upscale_size, self.target_upscale_size).to_pil().save(status.build_upscaled_path())
                    status.update()
                else:
                    image_to_upscale = BrainBoxTask.safe_id()+'.png'
                    builder.uploads[image_to_upscale] = status.cropped_path
                    upscale_dependency = builder.append(
                        Upscale(input_filename=image_to_upscale).as_brainbox_task(),
                        dict(type='upscale', target=status.build_upscaled_path())
                    )

            if status.interrogation_path is None:
                if upscale_dependency is not None:
                    argument = upscale_dependency
                else:
                    argument = BrainBoxTask.safe_id()+'.png'
                    builder.uploads[argument] = status.upscaled_path
                builder.append(BrainBoxTask.call(WD14Tagger).interrogate(
                    image = argument,
                    threshold=self.interrogation_threshold),
                    dict(type='interrogate', target=status.build_interrogation_path())
                )

        return builder.to_collector_pack('to_array')

    def apply_ai_pack(self, result):
        for item in result:
            if item['result'] is None:
                print(f"Job failed: {item}")
            if 'target' in item['tags']:
                os.makedirs(item['tags']['target'].parent, exist_ok=True)
            if item['tags']['type'] == 'upscale':
                try:
                    self.brainbox_api.download(item['result'].name, item['tags']['target'])
                except Exception as ex:
                    print(ex)
            if item['tags']['type'] == 'interrogate':
                FileIO.write_json(item['result'], item['tags']['target'])
            if item['tags']['type'] == 'tags':
                settings = AnnotationSettings.load(self.root_folder)
                settings.tags = [tag['name'] for tag in item['result']]
                settings.save()

    def run_ai(self):
        self._make_crops()
        pack = self.build_ai_pack()
        result = self.brainbox_api.execute(pack)
        self.apply_ai_pack(result)


    def run_croper(self):
        subprocess.call([
            sys.executable,
            Path(__file__).parent/'run_croper.py',
            self.root_folder,
        ])
        self._make_crops()


    def load_status(self):
        statuses = Status.gather_all(self.root_folder)

        table = ['<table>']
        table.append('''<tr>
            <td>Name</td>
            <td>Image</td>
            <td>Crop schema</td>
            <td>Cropped image</td>
            <td>Upscaled</td>
            <td>Interrogated</td>
            <td>Annotated</td>
            </tr>'''
        )

        def get_mark(file, content:object='', transform = None):
            if file is None or content is None:
                return '✗'
            if transform is None:
                return '✓'
            return transform(file, content)

        for status in statuses:
            table.append('<tr>')
            table.append(f'<td>{status.source_path.name[:20]}</td>')

            image = ConvertImage(status.source_path).resize_to_bounding(self.preview_size).to_html_tag()
            table.append(f'<td>{image}</td>')

            crop_schema = get_mark(status.crop_schema_path, status.crop_rect, lambda f,c: c.uuid)
            table.append(f'<td>{crop_schema}</td>')

            cropped_image = get_mark(
                status.cropped_path,
                transform=lambda f,c: ConvertImage(f).resize_to_bounding(self.preview_size).to_html_tag()
            )
            table.append(f'<td>{cropped_image}</td>')

            table.append(f'<td>{get_mark(status.upscaled_path)}</td>')
            table.append(f'<td>{get_mark(status.interrogation_path)}</td>')
            table.append(f'<td>{get_mark(status.annotation_path)}</td>')
            table.append("</tr>")
        table.append('</table>')

        return ''.join(table)


    @staticmethod
    def recode_bad_formats(root_folder, extension='.png'):
        folder = Path(root_folder)/Folders.source
        for file in os.listdir(folder):
            if file.endswith('.webp') or file.endswith('.avif'):
                name = file.replace('.webp',extension)
                ConvertImage(folder/file).to_pil().save(folder/name)
                os.unlink(folder/file)

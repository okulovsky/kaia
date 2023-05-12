from .conversion import ConvertImage
import ipywidgets
from yo_fluq_ds import FileIO, Query, fluq
import os
import pandas as pd
from PIL import Image

class EditingPanel:
    def __init__(self, source_folder, annotation_folder, rdf, interrogation_path, on_ok, ban_list):
        sdf =  rdf.loc[rdf.interrogation_path == interrogation_path]
        self.annotation_file = annotation_folder / sdf.annotation_path.iloc[0]
        self.image_file = source_folder/sdf.image_path.iloc[0]
        self.image = ConvertImage(self.image_file).to_pywidget()
        self.words = sdf.sort_values('scores', ascending=False).word.feed(list)
        self.edit = ipywidgets.Text()
        self.buttons = ipywidgets.VBox()
        self.ban_list = ban_list

        self.on_ok_event = on_ok

        self.ok = ipywidgets.Button(description='OK')
        self.ok.on_click(self._on_ok)

        self.skip = ipywidgets.Button(description='SKIP')
        self.skip.on_click(self._on_skip)

        self.ok.button_style = 'warning'
        self.load()



    def _on_ok(self, button):
        self.save(False)
        self.on_ok_event(button)

    def _on_skip(self, button):
        self.save(True)
        self.on_ok_event(button)

    def set_button_style(self, button):
        button.button_style = 'success' if self.allowed[button.description] else 'danger'

    def change(self, button):
        self.allowed[button.description] = not self.allowed[button.description]
        self.set_button_style(button)

    def save(self, skip):
        annot = dict(allowed=self.allowed, custom_text=self.edit.value, skip=skip)
        os.makedirs(self.annotation_file.parent, exist_ok=True)
        FileIO.write_json(annot, self.annotation_file)

    def load(self):
        if os.path.isfile(self.annotation_file):
            annot = FileIO.read_json(self.annotation_file)
            self.allowed = annot['allowed']
            self.edit.value = annot['custom_text']
        else:
            self.allowed = {}

        for w in self.words:
            if not w in self.allowed:
                self.allowed[w] = w not in self.ban_list

        buttons = Query.en(self.words).feed(fluq.partition_by_count(4)).select(self.make_buttons).to_list()
        self.buttons.children = buttons

    def make_buttons(self, words):
        buttons = []
        for w in words:
            button = ipywidgets.Button(
                description=w,
                layout=ipywidgets.Layout(flex_flow='row wrap'),
            )
            self.set_button_style(button)
            button.on_click(self.change)
            buttons.append(button)
        return ipywidgets.HBox(children=buttons)

    def render(self):
        return ipywidgets.HBox(children=[
            self.image,
            ipywidgets.VBox(children=[
                self.buttons,
                self.edit,
                ipywidgets.HBox(children=[
                    self.ok,
                    self.skip
                ])
            ])
        ])


class ImageTagAnnotator:
    def __init__(self, rdf, source_folder, annotation_folder, ban_list, run_in_sequential_order=False):
        self.rdf = rdf
        self.panel = ipywidgets.VBox()
        self.source_folder = source_folder
        self.annotation_folder = annotation_folder
        self.ban_list = ban_list
        self.run_in_sequential_order = run_in_sequential_order
        self.next_index = 0
        self.setup()


    def setup(self):
        if not self.run_in_sequential_order:
            self.seen_files = Query.folder(self.annotation_folder,'**/*').select(lambda z: str(z.relative_to(self.annotation_folder))).to_list()
            self.seen_files+=[s.replace('/','\\') for s in self.seen_files]
            self.seen_files = set(self.seen_files)

            self.rdf['has_file'] = self.rdf.annotation_path.isin(self.seen_files)
            not_annotated = self.rdf.loc[~self.rdf.has_file]

            if not_annotated.shape[0] == 0:
                not_annotated = None
            else:
                not_annotated = not_annotated.sample(1).interrogation_path.iloc[0]
        else:
            if self.next_index>=self.rdf.shape[0]:
                not_annotated = None
            else:
                not_annotated = self.rdf.interrogation_path.iloc[self.next_index]
                self.next_index+=1

        if not_annotated is not None:
            panel = EditingPanel(self.source_folder, self.annotation_folder, self.rdf, not_annotated, lambda _: self.setup(), self.ban_list)
            self.panel.children = [panel.render()]
        else:
            self.panel.children = [ipywidgets.Label("ALL DONE!")]
            return

    def render(self):
        return self.panel

    @staticmethod
    def read_tags(folder, suffix='.deepdanbooru.json', annotation_extention='.annotation.json'):
        def _read_file(file):
            js = FileIO.read_json(file)
            words = [z.strip() for z in js['caption'].split(',')]
            df = pd.DataFrame(dict(word=words))
            df['interrogation_path'] = str(file.relative_to(folder))
            df['image_path'] = df.interrogation_path.str.replace(suffix, '')
            df['category'] = file.parent.name
            df['annotation_path'] = df.interrogation_path.str.replace(suffix, annotation_extention)
            df['scores'] = 1
            return df

        df = (Query
              .folder(folder, '**/*' + suffix)
              .select(_read_file)
              .feed(list, pd.concat)
              )

        return df


    @staticmethod
    def export(df_path, image_path, annot_path, output_path):
        df = pd.read_parquet(df_path).drop_duplicates('interrogation_path')

        for cat in df.category.unique():
            qdf = df.loc[df.category == cat]
            folder = output_path / f'100_{cat}'
            os.makedirs(folder, exist_ok=True)
            for idx, row in enumerate(Query.df(qdf)):
                annot = FileIO.read_json(annot_path / row['annotation_path'])
                img = Image.open(image_path / row['image_path'])
                try:
                    if annot.get('skip', False):
                        continue
                    tags = [c for c, v in annot['allowed'].items() if v]
                    if annot['custom_text'] != '':
                        tags += [c.strip() for c in annot['custom_text'].split(',')]
                    FileIO.write_text(', '.join(tags), folder / f'{idx}.txt')
                    img.convert('RGB').save(folder / f'{idx}.jpg')
                except:
                    print(annot)
                    raise

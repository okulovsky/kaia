from kaia.brainbox.media_library import MediaLibrary
import gradio as gr
from pathlib import Path
import numpy as np
from yo_fluq_ds import *


class Annotator:
    def __init__(self,
                 feedback_file: Path,
                 lib: MediaLibrary,
                 names: Iterable[str]
                 ):
        self.feedback_file = feedback_file
        if not self.feedback_file.is_file():
            with open(self.feedback_file, 'w'):
                pass
        self.lib = lib
        self.df = lib.to_df()
        self.buttons_titles = ['SKIP'] + list(names)

    @staticmethod
    def load(filename):
        feedback = {}
        for option, file in Query.file.text(filename).select(lambda z: z.split('|')):
            if file not in feedback:
                feedback[file] = option
        return feedback


    def export(self, resulting_media_library_path: Path, test_split_relative_size=0.1):
        annotation = Annotator.load(Path('annotation.txt'))
        df = pd.Series(annotation).to_frame('speaker')
        df = df.loc[df.speaker != 'SKIP']
        df.index.name = 'filename'
        df = df.reset_index()
        df = df.feed(fluq.add_ordering_column('speaker', 'filename'))
        df = df.merge(df.groupby('speaker').size().to_frame('total'), left_on='speaker', right_index=True)
        df['split'] = np.where(df.order <= df.total * test_split_relative_size, 'test', 'train')

        records = []
        for row in Query.df(df):
            record = self.lib[row.filename]
            record.tags['speaker'] = row.speaker
            record.tags['split'] = row.split
            records.append(record)

        resulting_lib = MediaLibrary(tuple(records))
        resulting_lib.save(resulting_media_library_path)

    def _append(self, option, file):
        with open(self.feedback_file, 'a') as stream:
            stream.write(f'{option}|{file}\n')

    def _next_sample(self):
        feedback = Annotator.load(self.feedback_file)
        df = self.df.loc[~self.df.filename.isin(feedback)]
        progress = 1 - df.shape[0] / self.df.shape[0]
        if df.shape[0] == 0:
            result = {
                self.controls.progress: progress,
                self.controls.audio: gr.update(interactive=False),
                self.controls.filename: gr.update(value='ALL DONE', visible=True)
            }
            for button in self.buttons:
                result[button] = gr.update(interactive=False)
            return result

        filename = df.sample(1).filename.iloc[0]
        audio_file = self.lib[filename].get_full_path()
        return {
            self.controls.progress: progress,
            self.controls.filename: filename,
            self.controls.audio: gr.update(
                value=audio_file,
                interactive=False,
                waveform_options=None,
                autoplay=True,
            )
        }

    def generate_interface(self, block):
        self.controls = Obj()
        self.controls.progress = gr.Slider(interactive=False, minimum=0, maximum=1)
        self.controls.audio = gr.Audio()
        self.controls.filename = gr.Label(visible=False)
        self.buttons = []
        with gr.Row():
            for title in self.buttons_titles:
                self.buttons.append(gr.Button(value=title, interactive=True))

        outputs = list(self.controls.values()) + self.buttons
        for button in self.buttons:
            (
                button
                .click(self._append, inputs=[button, self.controls.filename])
                .then(self._next_sample, outputs=outputs)
            )
        block.load(self._next_sample, outputs=outputs)

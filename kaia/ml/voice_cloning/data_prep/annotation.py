import numpy as np
from pathlib import Path
from kaia.infra import FileIO
from kaia.brainbox import MediaLibrary
from yo_fluq_ds import *
import gradio as gr


class AudioAnnotator:
    def __init__(self,
                 lib: MediaLibrary,
                 feedback_file: Path,
                 samples_folder: Optional[Path],
                 ):
        self.lib = lib
        self.df = lib.to_df()
        self.lib_dict = lib.mapping
        self.feedback_file = feedback_file
        if not self.feedback_file.is_file():
            FileIO.write_text('', self.feedback_file)
        self.options = ['ban','skip', 'bad', 'ok', 'good']

        self.add_samples = samples_folder is not None
        self.samples = {}
        if self.add_samples:
            for voice in self.df.voice.unique():
                self.samples[voice] = Query.folder(samples_folder / voice).to_list()


    @staticmethod
    def load(filename, feedback = None):
        if feedback is None:
            feedback = {}
        for key, id in Query.file.text(filename).select(lambda z: z.split('|')):
            if key not in feedback:
                feedback[key] = []
            feedback[key].append(id)
        return feedback

    def _append(self, key, id):
        with open(self.feedback_file, 'a') as stream:
            stream.write(f'{key}|{id}\n')

    def _get_sample_voice_file(self, voice):
        if self.add_samples:
            return self.samples[voice][np.random.randint(len(self.samples[voice]))]
        return None

    def _next_sample(self, voice):
        feedback = AudioAnnotator.load(self.feedback_file)
        for option in self.options:
            if option not in feedback:
                feedback[option] = []
        banned_texts = self.df.loc[self.df.filename.isin(feedback['ban'])].text.unique()
        df = self.df.loc[self.df.voice == voice]
        total = df.shape[0]
        total_texts = len(df.text.unique())
        unavailable_texts = df.loc[df.filename.isin(feedback["good"])].text.unique()

        available_rows = df.loc[
            ~df.text.isin(unavailable_texts) &
            ~df.filename.isin(feedback["bad"]) &
            ~df.filename.isin(feedback["ok"]) &
            ~df.text.isin(banned_texts)
            ]
        remaining = available_rows.shape[0]
        if available_rows.shape[0] == 0:
            return {button: gr.update(interactive=False) for button in self.buttons}

        row_num = np.random.randint(available_rows.shape[0])
        stats = f'{total - remaining}/{total}, {len(unavailable_texts)}/{total_texts} good texts'
        return self._create_sample(available_rows.iloc[row_num], total, remaining, stats)

    def _create_sample(self, row, total, remaining, stats):
        text = row.text
        filename = row.filename
        audio_file = self.lib_dict[filename].get_full_path()
        reply = {
            self.controls.sample_voice: gr.update(value=self._get_sample_voice_file(row.voice), autoplay=False),
            self.controls.audio: gr.update(value=audio_file, interactive=False, waveform_options=None, autoplay=True,
                                           label=text),
            self.controls.filename: filename,
        }
        if total is not None and remaining is not None:
            reply[self.controls.progress] = gr.update(label=stats, value=total - remaining, maximum=total)

        for button in self.buttons:
            reply[button] = gr.update(interactive=True)
        return reply

    def _change_sample_voice(self, voice):
        if isinstance(voice, list) or voice not in self.samples:
            return gr.update()
        return gr.update(value=self._get_sample_voice_file(voice), autoplay=True)

    def generate_interface(self):
        voices = gr.Dropdown(choices=list(self.df.voice.unique()), multiselect=False, label='Voice')

        self.controls = Obj()
        self.controls.progress = gr.Slider(interactive=False)
        self.controls.audio = gr.Audio()
        self.controls.filename = gr.Label(visible=False)
        self.buttons = []
        with gr.Row():
            for field in list(self.options):
                self.buttons.append(gr.Button(value=field, interactive=False))
        self.controls.sample_voice = gr.Audio(label='Reference voice')
        change_sample_voice = gr.Button(value="Change sample voice")
        change_sample_voice.click(self._change_sample_voice, inputs=voices, outputs=self.controls.sample_voice)

        get_sample_args = (self._next_sample, voices, list(self.controls.values()) + list(self.buttons))

        voices.change(*get_sample_args)
        for button in self.buttons:
            if button.value == 'skip':
                button.click(*get_sample_args)
            else:
                (
                    button
                    .click(self._append, inputs=[button, self.controls.filename])
                    .then(*get_sample_args)
                )
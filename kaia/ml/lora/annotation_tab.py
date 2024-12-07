from kaia.infra.gradio import empty_handler
import gradio as gr
from pathlib import Path
from dataclasses import dataclass
from kaia.infra import FileIO
from yo_fluq_ds import Obj
from PIL import Image
from kaia.ml.lora import AnnotationController

class AnnotationView:
    def __init__(self, controller: AnnotationController):
        self.controller = controller
        self.main_controls = []
        self.tag_buttons = []
        self.button_rows = 30
        self.button_columns = 3

    def new_tags_change(self, tags):
        self.controller.current.stored.new_tags = tags

    def banned_tags_change(self, tags):
        self.controller.annotation_settings.exclude_tags = tags

    def global_tags_change(self, tags):
        self.controller.annotation_settings.include_tags = tags


    def on_click(self, tag):
        new_status = self.controller.current.change_status(tag)
        return gr.update(visible=True, value=tag, elem_classes=f'button_{new_status}')

    def load_main(self):
        return {
            self.image_control: (
                self.controller.current.status.upscaled_path
                if self.controller.current.status.upscaled_path is not None
                else self.controller.current.status.cropped_path
            ),
            self.new_tags: gr.update(
                value=self.controller.current.stored.new_tags,
                choices=self.controller.annotation_settings.tags),
            self.banned_tags: gr.update(
                value=self.controller.annotation_settings.exclude_tags,
                choices=self.controller.annotation_settings.tags
            ),
            self.global_tags: gr.update(
                value=self.controller.annotation_settings.include_tags,
                choices=self.controller.annotation_settings.tags
            ),
            self.reviewed_control: self.controller.current.stored.reviewed,
            self.skipped_control: self.controller.current.stored.skipped,
        }

    def load_buttons(self):
        tags = self.controller.current.get_tags_list()
        result = {}
        for i, button in enumerate(self.tag_buttons):
            if i < len(tags):
                result[button] = gr.update(visible=True, value=tags[i].name, elem_classes=f'button_{tags[i].status}')
            else:
                result[button] = gr.update(visible=False)
        return result

    def setup_load_main(self, endpoint):
        return (endpoint
                .then(self.load_main, outputs=self.main_controls)
                .then(self.load_buttons, outputs=self.tag_buttons)
                )

    def skipped_change(self, skipped):
        if not isinstance(skipped, bool):
            raise ValueError()
        self.controller.current.stored.skipped = skipped

    def cm_save(self):
        self.controller.save()

    def cm_previous(self):
        self.controller.change_index(-1)

    def cm_next(self):
        self.controller.change_index(1)

    def generate_interface(self):
        with gr.Row():
            with gr.Column():
                self.image_control = gr.Image(width=512, height=512)
                self.main_controls.append(self.image_control)
                self.reviewed_control = gr.Checkbox(label='Reviewed', interactive=True)
                self.main_controls.append(self.reviewed_control)
                self.skipped_control = gr.Checkbox(label='Skip', interactive=True)
                self.main_controls.append(self.skipped_control)
                self.new_tags = gr.Dropdown(multiselect=True, label='Manually entered tags', allow_custom_value=True)
                self.main_controls.append(self.new_tags)
                self.banned_tags = gr.Dropdown(multiselect=True, label='Globally banned tags', allow_custom_value=True)
                self.main_controls.append(self.banned_tags)
                self.global_tags = gr.Dropdown(multiselect=True, label='Globally applied tags', allow_custom_value=True)
                self.main_controls.append(self.global_tags)
                with gr.Row():
                    self.prev_button = gr.Button(value='PREV')
                    self.save_button = gr.Button(value="SAVE")
                    self.next_button = gr.Button(value='NEXT')
            with gr.Column():
                for row in range(self.button_rows):
                    with gr.Row():
                        for column in range(self.button_columns):
                            button = gr.Button()
                            button.click(self.on_click, inputs=[button], outputs=[button])
                            self.tag_buttons.append(button)

        self.new_tags.change(self.new_tags_change, inputs=[self.new_tags])
        self.banned_tags.change(self.banned_tags_change, inputs=[self.banned_tags]).feed(self.setup_load_main)
        self.global_tags.change(self.global_tags_change, inputs=[self.global_tags]).feed(self.setup_load_main)
        self.prev_button.click(self.cm_save).then(self.cm_previous).feed(self.setup_load_main)
        self.save_button.click(self.cm_save).feed(self.setup_load_main)
        self.next_button.click(self.cm_save).then(self.cm_next).feed(self.setup_load_main)
        self.skipped_control.change(self.skipped_change, inputs=[self.skipped_control])

    def create_css(self):
        status_to_color = {True: '#cfc', False: '#fcc'}
        css_lines = []
        for status in [True, False]:
            css_lines.append(f'.button_{status} {{ background-color: {status_to_color[status]}; background-image: none; }}')
        return '\n'.join(css_lines)


    def create_demo(self):
        with gr.Blocks(css=self.create_css()) as demo:
            view = AnnotationView(self.controller)
            view.generate_interface()
            demo.load(empty_handler).feed(view.setup_load_main)
        return demo


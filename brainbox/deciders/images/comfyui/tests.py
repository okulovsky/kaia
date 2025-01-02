from ....framework import BrainBox, TestReport, File
from .workflows import *
from unittest import TestCase
from pathlib import Path


class Test:
    def __init__(self, api: BrainBox.Api, tc: TestCase):
        self.api = api
        self.tc = tc

    def test_generation(self):
        prompt = "cute little cat playing with a woolball, solo, no humans, animal, cat"
        negative_prompt = "bad quality, dull colors, monochrome, boy, girl, people, nsfw, nudity"
        model = 'meinamix_meinaV9.safetensors'
        self.api.execute(TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            model=model,
            seed=42

        ))
        yield (TestReport
               .last_call(self.api)
               .result_is_array_of_files(File.Kind.Image)
               )

        self.api.execute(TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            lora_01='cat_lora.safetensors',
            model=model
        ))

        yield (TestReport
               .last_call(self.api)
               .result_is_array_of_files(File.Kind.Image)
               .with_comment("Test to image workflow, with LoRA")
               )


    def test_upscale_and_interrogate(self):
        source_image = File.read(Path(__file__).parent / 'image.png')
        input_name = BrainBox.Task.safe_id() + '.png'
        self.api.upload(input_name, source_image)
        self.api.execute(Upscale(input_name))
        yield (TestReport
               .last_call(self.api)
               .result_is_file(File.Kind.Image)
               .with_uploaded_file(input_name, source_image)
               .with_comment("Upscaling workflow")
               )


        self.api.execute(WD14Interrogate(input_name))
        yield (TestReport
               .last_call(self.api)
               .with_uploaded_file(input_name, source_image)
               .with_comment("Interrogation with WD14")
               )



    def test_all(self):
        yield TestReport.main_section_content("All ComfyUI functionality is accessible via the same endpoint. The workflow is actvated depending on `workflow_type` parameter")
        yield from self.test_generation()
        yield from self.test_upscale_and_interrogate()

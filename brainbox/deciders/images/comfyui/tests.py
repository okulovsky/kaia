from ....framework import BrainBox, TestReport, File
from .workflows import *
from unittest import TestCase
from pathlib import Path


class Test:
    def __init__(self, api: BrainBox.Api, tc: TestCase):
        self.api = api
        self.tc = tc

    def test_generation(self):
        yield TestReport.H1("Text to image")
        prompt = "cute little cat playing with a woolball, solo, no humans, animal, cat"
        yield TestReport.text("Prompt")
        yield TestReport.code(prompt)
        negative_prompt = "bad quality, dull colors, monochrome, boy, girl, people, nsfw, nudity"
        yield TestReport.text("Negative prompt")
        yield TestReport.code(negative_prompt)

        model_name = 'meinamix_meinaV9.safetensors'
        yield TestReport.H2(f"Model {model_name}")
        results = self.api.execute(TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            model=model_name,
            seed=42

        ))
        for result in results:
            yield TestReport.file(self.api.download(result))

        yield TestReport.H2(f"With LoRA")
        results = self.api.execute(TextToImage(
            prompt=prompt,
            negative_prompt=negative_prompt,
            batch_size=2,
            lora_01='cat_lora.safetensors',
            model=model_name
        ))

        for result in results:
            yield TestReport.file(self.api.download(result))

    def test_upscale_and_interrogate(self):
        yield TestReport.H1("Upscale")
        source_image = Path(__file__).parent / 'image.png'
        yield TestReport.text("Source image")
        yield TestReport.file(File.read(source_image))
        input_name = BrainBox.Task.safe_id() + '.png'
        self.api.upload(input_name, source_image)
        upscaled = self.api.execute(Upscale(input_name))
        yield TestReport.text("Upscaled image")
        yield TestReport.file(self.api.download(upscaled))

        yield TestReport.H1("WD14 Interrogate")
        yield TestReport.text("Source image")
        yield TestReport.file(File.read(source_image))

        interrogation = self.api.execute(WD14Interrogate(input_name))
        yield TestReport.json(interrogation)



    def test_all(self):
        yield from self.test_generation()
        yield from self.test_upscale_and_interrogate()

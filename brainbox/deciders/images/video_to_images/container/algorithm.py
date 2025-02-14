import cv2
import json
import os
import shutil
from PIL import Image
from settings import AnalysisSettings
from frame import Frame
from layer_capture import layer_capture
from layer_bufferer import layer_bufferer
from layer_semantic_comparator import layer_comparator

class VideoProcessorApp:
    def __init__(self):
        self.input_directory = '/resources/input'
        self.output_directory = '/resources/output/images'
        self.timestamps = '/resources/output/frames.jsonl'
        self.settings_file = '/resources/settings.json'
        os.makedirs(self.output_directory, exist_ok=True)


    def run(self):
        with open(self.settings_file,'r') as file:
            settings = AnalysisSettings(**json.load(file))

        source = layer_capture(settings)
        if settings.buffer_by_laplacian_in_ms is not None:
            source = layer_bufferer(source, settings.buffer_by_laplacian_in_ms, 'laplacian')
        if settings.add_semantic_comparator:
            source = layer_comparator(source)

        with open(self.timestamps, 'w') as stream:
            for index, frame in enumerate(source):
                if settings.max_produced_frames is not None and index>=settings.max_produced_frames:
                    print(f"Interrupting at {index} >= {settings.max_produced_frames}")
                    break

                frame.pil_image.save(os.path.join(self.output_directory, frame.filename), format="PNG")
                data = frame.__dict__
                del data['frame']
                del data['pil_image']
                stream.write(json.dumps(data))
                stream.write('\n')
                stream.flush()




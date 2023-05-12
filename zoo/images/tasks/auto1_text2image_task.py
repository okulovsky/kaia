from typing import *
from kaia.infra.tasks import ITask, ProgressReporter
from copy import deepcopy
from ..tools import ConvertImage
from .automatic1111 import Automatic1111


class Auto1TextToImage(ITask):
    def __init__(self,
                 base_settings: Any = None,
                 ):
        if base_settings is None:
            base_settings = DEFAULT_SETTINGS
        self.settings = base_settings

    def warm_up(self):
        Automatic1111.run_if_absent()

    def run(self, reporter: ProgressReporter, settings: Dict, convert_to_PIL = True):
        final_settings = deepcopy(self.settings)
        final_settings.update(**settings)
        rq = Automatic1111.run_request('/sdapi/v1/txt2img', settings, reporter)
        reporter.report_progress(1)
        reporter.finish()
        if not convert_to_PIL:
            return rq['images']
        else:
            return [ConvertImage.from_base64(img) for img in rq['images']]



DEFAULT_SETTINGS = {'prompt': '',
 'styles': [],
 'negative_prompt': '',
 'seed': -1,
 'subseed': -1.0,
 'subseed_strength': 0,
 'seed_resize_from_h': 0,
 'seed_resize_from_w': 0,
 'sampler_name': 'DPM++ 2M Karras',
 'batch_size': 1,
 'n_iter': 1,
 'steps': 32,
 'cfg_scale': 11.5,
 'width': 512,
 'height': 512,
 'restore_faces': False,
 'tiling': False,
 'enable_hr': False,
 'denoising_strength': 0.61,
 'hr_scale': 2,
 'hr_upscaler': 'Latent',
 'hr_second_pass_steps': 0,
 'hr_resize_x': 0,
 'hr_resize_y': 0,
 'override_settings': {'CLIP_stop_at_last_layers': 2,
  'eta_noise_seed_delta': 31337,
  'always_discard_next_to_last_sigma': True}
                    }





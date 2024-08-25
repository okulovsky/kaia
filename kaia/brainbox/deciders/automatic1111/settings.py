from dataclasses import dataclass, field

@dataclass
class Automatic1111Model:
    url: str
    filename: str | None = None


    def __post_init__(self):
        if self.filename is None:
            self.filename = self.url.split('/')[-1]


def _default_sd_models() -> tuple[Automatic1111Model,...]:
    return (
        Automatic1111Model("https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"),
        Automatic1111Model('https://civitai.com/api/download/models/17233', 'abyssorangemix3-aom3.safetensors'),
    )


@dataclass
class Automatic1111Settings:
    port = 11009
    sd_models_to_download: tuple[Automatic1111Model,...] = field(default_factory=_default_sd_models)
    default_request: dict = field(default_factory=lambda: DEFAULT_REQUEST)



DEFAULT_REQUEST = {
  "prompt": "",
  "negative_prompt": "",
  "styles": [
  ],
  "seed": -1,
  "subseed": -1,
  "subseed_strength": 0,
  "seed_resize_from_h": -1,
  "seed_resize_from_w": -1,
  "batch_size": 1,
  "n_iter": 1,
  "steps": 50,
  "cfg_scale": 7,
  "width": 512,
  "height": 512,
  "restore_faces": True,
  "tiling": True,
  "do_not_save_samples": False,
  "do_not_save_grid": False,
  "eta": 0,
  "denoising_strength": 0,
  "s_min_uncond": 0,
  "s_churn": 0,
  "s_tmax": 0,
  "s_tmin": 0,
  "s_noise": 0,
  "override_settings": {},
  "override_settings_restore_afterwards": True,
  "refiner_switch_at": 0,
  "disable_extra_networks": False,
  "firstpass_image": "string",
  "comments": {},
  "enable_hr": False,
  "firstphase_width": 0,
  "firstphase_height": 0,
  "hr_scale": 2,
  "hr_upscaler": "string",
  "hr_second_pass_steps": 0,
  "hr_resize_x": 0,
  "hr_resize_y": 0,
  "hr_prompt": "",
  "hr_negative_prompt": "",
  "sampler_index": "Euler",
  "script_args": [],
  "send_images": True,
  "save_images": False,
  "alwayson_scripts": {},
}
from .collector import Collector, CollectorTaskBuilder, FunctionalTaskBuilder
from .comfyui import ComfyUIInstaller, ComfyUISettings, ComfyUI, TextToImage, WD14Interrogate, Upscale, ComfyUIUtils
from .coqui_tts import CoquiTTS, CoquiTTSInstaller, CoquiTTSSettings
from .ollama import Ollama, OllamaInstaller, OllamaSettings
from .open_tts import OpenTTS, OpenTTSInstaller, OpenTTSSettings
from .resemblyzer import Resemblyzer, ResemblyzerSettings, ResemblyzerInstaller
from .rhasspy_kaldi import RhasspyKaldiInstaller, RhasspyKaldi, RhasspyKaldiSettings
from .tortoise_tts import TortoiseTTS, TortoiseTTSSettings, TortoiseTTSInstaller
from .whisper import Whisper, WhisperInstaller, WhisperSettings, WhisperExtendedAPI

from .collector import Collector
from .fake_dub_decider import FakeDubDecider
from .fake_image_generator import FakeImageDecider
from .fake_llm_decider import FakeLLMDecider
from .output_translator import OutputTranslator


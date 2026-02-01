import os
from modelscope import snapshot_download as snapshot_download_modelscope
from huggingface_hub import snapshot_download


def install():
    snapshot_download_modelscope("pengzhendong/wetext")

    snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='/resources/pretrained_models/Fun-CosyVoice3-0.5B')
    snapshot_download('FunAudioLLM/CosyVoice2-0.5B', local_dir='/resources/pretrained_models/CosyVoice2-0.5B')
    snapshot_download('FunAudioLLM/CosyVoice-300M', local_dir='/resources/pretrained_models/CosyVoice-300M')
    snapshot_download('FunAudioLLM/CosyVoice-300M-SFT', local_dir='/resources/pretrained_models/CosyVoice-300M-SFT')
    snapshot_download('FunAudioLLM/CosyVoice-300M-Instruct', local_dir='/resources/pretrained_models/CosyVoice-300M-Instruct')
    snapshot_download('FunAudioLLM/CosyVoice-ttsfrd', local_dir='/resources/pretrained_models/CosyVoice-ttsfrd')

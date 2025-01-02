from kaia.kaia.audio_control.wav_streaming import WavStreamingApi, WavStreamingServer, WavServerSettings, WavApiSettings
from .app import KaiaApp

def set_streaming_service_and_api_address(app:KaiaApp):
    server = WavStreamingServer(WavServerSettings(app.brainbox_cache_folder))
    app.wav_streaming_server = server
    app.wav_streaming_api =  WavStreamingApi(WavApiSettings())

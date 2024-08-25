from kaia.kaia.audio_control.wav_streaming import WavStreamingApi, WavStreamingServer, WavServerSettings, WavApiSettings

def create_wav_streaming_service_and_api_address(cache_folder):
    server = WavStreamingServer(WavServerSettings(cache_folder))
    address = WavStreamingApi(WavApiSettings()).settings.address
    return server, address

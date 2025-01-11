from brainbox.deciders.voice_generation.open_tts import OpenTTS

if __name__ == '__main__':
    installer = OpenTTS.Controller()
    installer.install()
    installer.self_test()


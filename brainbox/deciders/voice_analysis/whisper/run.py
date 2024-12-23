from brainbox.deciders.voice_analysis.whisper import Whisper

if __name__ == '__main__':
    controller = Whisper.Controller()
    controller.install()
    controller.self_test()

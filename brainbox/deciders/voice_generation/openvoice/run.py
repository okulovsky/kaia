from brainbox.deciders import OpenVoice

if __name__ == "__main__":
    controller = OpenVoice.Controller()
    controller.install()
    controller.self_test()

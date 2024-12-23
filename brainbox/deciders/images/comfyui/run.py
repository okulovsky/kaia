from brainbox.deciders import ComfyUI
import webbrowser


if __name__ == '__main__':
    controller = ComfyUI.Controller()
    controller.install()
    controller.self_test()





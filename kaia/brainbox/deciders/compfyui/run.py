from kaia.brainbox.deciders.compfyui import ComfyUIInstaller, ComfyUISettings, ComfyUI
import webbrowser


if __name__ == '__main__':
    installer = ComfyUIInstaller(ComfyUISettings())
    installer.install()
    installer.brainbox_self_test()



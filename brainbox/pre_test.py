from brainbox.deciders import HelloBrainBox
from brainbox import BrainBox


if __name__ == '__main__':
    with BrainBox.Api.test() as api:
        api.controllers.install.execute(HelloBrainBox)


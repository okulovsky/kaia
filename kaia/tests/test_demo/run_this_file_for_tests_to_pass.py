# Each run of the Demo server requires BrainBox to start some deciders in the ready stage
# It takes some time, and while it's normal for the production, it's a bit too long for the tests.
# Thus, for tests this initialization is excluded, but you have to run it manually.
from kaia.demo.core import get_controller_setup
from brainbox import BrainBox

if __name__ == '__main__':
    with BrainBox.Api.Test(always_on_planner=True) as api:
        api.controller_api.setup(get_controller_setup())

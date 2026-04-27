from brainbox.framework import (
    BrainBoxServer, ControllerRegistry, BrainBoxServerSettings, BrainBoxLocations,
    SimplePlanner, AlwaysOnPlanner
)

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--data-folder', required=True)
parser.add_argument('-p', '--port', default='8090')
parser.add_argument('-l', '--planer', default='standard')

if __name__ == '__main__':
    args = parser.parse_args()
    port = int(args.port)
    data_folder = Path(args.data_folder)

    planer_str = args.planer
    if planer_str == 'standard':
        planer = SimplePlanner()
    elif planer_str == 'always_on_find_only':
        planer = AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindOnly)
    elif planer_str == 'always_on_start_only':
        planer = AlwaysOnPlanner(AlwaysOnPlanner.Mode.StartOnly)
    elif planer_str == 'always_on_find_then_start':
        planer = AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart)
    else:
        raise ValueError(f"Unknown planner {planer_str}")


    locations = BrainBoxLocations.default(data_folder)
    registry = ControllerRegistry.discover(data_folder/'resources')
    settings = BrainBoxServerSettings(
        planner=planer,
        registry=registry,
        locations=locations,
        port=port
    )
    server = BrainBoxServer(settings)
    server()

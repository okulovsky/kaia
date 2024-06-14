from kaia.brainbox.test_cases import execute_tests, create_cases
from kaia.brainbox.core import BrainBoxTestApi
from kaia.brainbox import BrainBox
from kaia.infra import Loc, FileIO
from pathlib import Path

if __name__ == '__main__':
    box = BrainBox()
    #with Loc.create_temp_folder('tests/brain_box_integration') as folder:
    #    with BrainBoxTestApi(box.create_deciders_dict(), folder) as api:

    api = box.create_api('127.0.0.1')
    cases = list(create_cases())
    result = execute_tests(cases, api)
    FileIO.write_pickle(result, Loc.root_folder/'demos/brainbox/files/cases.pkl')


from kaia.brainbox.deciders.compfyui.workflows.wd14_interrogate import WD14Interrogate
from pprint import pprint

if __name__ == '__main__':
    obj = WD14Interrogate('test')
    pprint(obj.create_workflow_json('ABC',None))

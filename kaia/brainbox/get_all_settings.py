from kaia.brainbox import BrainBox

if __name__ == '__main__':
    settings = BrainBox().settings
    for field, value in settings.__dict__.items():
        if type(value).__name__.endswith('Settings'):
            for sfield, svalue in value.__dict__.items():
                if 'port' in sfield:
                    print(f'{field} {sfield} = {svalue}')

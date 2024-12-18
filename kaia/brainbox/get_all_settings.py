from kaia.brainbox import BrainBox

if __name__ == '__main__':
    deciders = BrainBox().create_deciders_dict()
    for key, value in deciders.items():
        settings = getattr(value, 'settings', None)
        if settings is None:
            continue
        for field, value in settings.__dict__.items():
            if 'port' in field:
                print(f'{field} {field} = {value}')

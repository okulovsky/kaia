import argparse
import json

from functions import Functions
from settings import TrainingSettings
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset')
    parser.add_argument('-c', '--export', action='store_true')
    parser.add_argument('-f', '--working-folder', default='/resources')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.export:
        export_path = Path(args.working_folder)
        f = Functions(args.dataset, args.working_folder, None)
        print(f'EXPORTING DATASET {f.dataset}')
        f.export_model()
        exit(0)

    settings_path = Path(args.working_folder)/'trainings'/args.dataset/'settings.json'
    with open(settings_path,'r') as stream:
        settings_js = json.load(stream)
    settings = TrainingSettings(**settings_js)
    print("Training settings:")
    print(settings)

    f = Functions(args.dataset, args.working_folder, settings)
    print(f'DATASET {f.dataset}')
    if not settings.continue_existing:
        print('PREPROCESSING')
        f.preprocess()
    print('TRAINING')
    f.train()




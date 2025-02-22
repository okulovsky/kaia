import argparse
import json

from functions import Functions
from settings import TrainingSettings
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset')
    parser.add_argument('-c', '--convert')
    parser.add_argument('-f', '--working-folder', default='/resources')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    if args.dataset is not None:
        settings_path = Path(args.working_folder)/'trainings'/args.dataset/'settings.json'
        with open(settings_path,'r') as stream:
            settings_js = json.load(stream)
        settings = TrainingSettings(**settings_js)
        print("Training settings:")
        print(settings)

        f = Functions(args.dataset, args.working_folder, settings)
        print(f'DATASET {f.dataset}')
        print('PREPROCESSING')
        f.preprocess()
        print('TRAINING')
        f.train()
        print('EXPORTING')
        f.export_model()

    if args.convert is not None:
        Functions.convert_custom_filename(Path(args.working_folder)/'conversions'/args.convert)







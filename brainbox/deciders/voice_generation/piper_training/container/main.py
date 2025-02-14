import argparse
from functions import Functions
from settings import TrainingSettings

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset')
    parser.add_argument('-f', '--working-folder', default='/resources')

    args = parser.parse_args()
    print(f"Running with arguments\n{args}")

    f = Functions(args.dataset, args.working_folder, TrainingSettings())
    print(f'DATASET {f.dataset}')
    print('PREPROCESSING')
    f.preprocess()
    print('TRAINING')
    f.train()
    print('EXPORTING')
    f.export_model()








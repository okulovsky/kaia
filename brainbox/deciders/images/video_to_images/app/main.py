
from algorithm import VideoProcessorApp
import argparse
from layer_semantic_comparator import get_comparator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', '-i', action='store_true')
    args = parser.parse_args()

    if args.install:
        get_comparator()
        exit(0)


    app = VideoProcessorApp()
    app.run()


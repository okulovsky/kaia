from server import VideoProcessorApp
import argparse
from model import get_comparator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--install', '-i', action='store_true')
    args = parser.parse_args()

    if args.install:
        get_comparator()
        exit(0)


    app = VideoProcessorApp()
    app.run(args.file)


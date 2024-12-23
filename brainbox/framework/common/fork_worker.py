import sys
import pickle
import os
import traceback

if __name__ == '__main__':
    file = sys.argv[1]
    with open(file, 'rb') as stream:
        method = pickle.load(stream)
    os.unlink(file)
    try:
        method()
    except:
        print(traceback.format_exc(), file=sys.stderr)
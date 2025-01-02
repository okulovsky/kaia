import sys
import pickle
import os
import traceback

if __name__ == '__main__':
    name = sys.argv[1]
    file = sys.argv[2]

    try:
        with open(file, 'rb') as stream:
            method = pickle.load(stream)
        os.unlink(file)
    except:
        print(f"Subprocess for {name}: cannot read entry point", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise

    try:
        method()
    except:
        print(f"Subprocess for {name}: exception in entry point", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise



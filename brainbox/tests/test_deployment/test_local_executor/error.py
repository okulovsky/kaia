import sys

if __name__ == '__main__':
    print("STDOUT")
    print('STDERR', file=sys.stderr)
    raise ValueError("")
import sys
import time

if __name__ == '__main__':
    print('STDOUT')
    time.sleep(1)
    print('STDERR', file=sys.stderr)
    time.sleep(0.1)
    print('NO_ERROR')
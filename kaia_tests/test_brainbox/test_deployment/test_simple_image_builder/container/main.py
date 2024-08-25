import os
import sys
import subprocess

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Provide a command line argument')
        exit(0)

    print('Writing outbiund file...', end='')
    os.makedirs('/home/app/data/test/', exist_ok=True)
    with open('/home/app/data/test/test.txt','w') as file:
        file.write("outer: "+sys.argv[1])
    print('DONE')

    print('Writing local file...', end='')
    with open('/home/app/local','w') as file:
        file.write("inner: "+sys.argv[1])
    print("DONE")

    print('Importing pandas...', end='')
    import pandas
    print('DONE')

    print(subprocess.check_output(['groups']))



    print('Exiting')



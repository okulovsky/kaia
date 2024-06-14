import sys
import subprocess
from server import WhisperApp

if __name__ == '__main__':
    print(f"Running with arguments\n{sys.argv}")

    if len(sys.argv) == 1:
        print("Running web-server")
        factory = WhisperApp()
        factory.create_app().run('0.0.0.0', 8084)
        exit(0)

    if len(sys.argv) == 2:
        if sys.argv[1] == 'notebook':
            subprocess.call(['jupyter','notebook','--allow-root','--port','8899', '--ip', '0.0.0.0'], cwd='/repo')
            exit(0)
        else:
            raise ValueError('If one argument is provided, it should be `notebook`')
    else:
        raise ValueError(f'Unexpected arguments: {sys.argv}')

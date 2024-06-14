import subprocess
import sys
from server import SnipsNLUWebApp

if __name__ == '__main__':
    if len(sys.argv) == 1:
        app = SnipsNLUWebApp().create_app()
        app.run('0.0.0.0', 8084)
    elif len(sys.argv) == 2 and sys.argv[1] == 'notebook':
        subprocess.call(['jupyter','notebook','--allow-root','--port','8899', '--ip', '0.0.0.0'], cwd='/repo')
    else:
        raise ValueError(f'Unexpected arguments {sys.argv}')
from .loc import Loc
from pathlib import Path
import subprocess
import os
import stat

class ConsoleExecutor:
    wait = False
    @staticmethod
    def execute(cmd, folder = None):
        if Loc.is_windows:
            bat_location = Loc.temp_folder/'_start.bat'
            with open(bat_location,'w') as file:
                file.write(cmd)
                if ConsoleExecutor.wait:
                    file.write('\npause')
            kw = {}
            if folder is not None:
                kw['cwd']=folder
            subprocess.call([bat_location], creationflags=subprocess.CREATE_NEW_CONSOLE, **kw)
        else:
            if ConsoleExecutor.wait:
                cmd+='; exec bash'
            args = ['gnome-terminal', '--', '/bin/sh', '-c', "'"+cmd+"'"]
            cur_dir = os.getcwd()
            if folder is not None:
                os.chdir(folder)
            os.system(' '.join(args))
            os.chdir(cur_dir)


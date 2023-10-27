from ..loc import Loc
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
            sh_location = Loc.temp_folder/'_start.sh'
            with open(sh_location,'w') as file:
                file.write(cmd)
                if ConsoleExecutor.wait:
                    file.write('\necho Press ENTER to close')
                    file.write('\nread')
            os.chmod(sh_location, 0o777)
            if folder is not None:
                os.chdir(folder)
            os.system(f"gnome-terminal --wait -- bash -c '{sh_location}; exit'")


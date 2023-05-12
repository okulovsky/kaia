from .loc import Loc
from pathlib import Path
import subprocess

class ConsoleExecutor:
    wait = False
    @staticmethod
    def execute(cmd, folder = None):
        bat_location = Loc.temp_folder/'_start.bat'
        with open(bat_location,'w') as file:
            file.write(cmd)
            if ConsoleExecutor.wait:
                file.write('\npause')
        kw = {}
        if folder is not None:
            kw['cwd']=folder
        subprocess.call([bat_location], creationflags=subprocess.CREATE_NEW_CONSOLE, **kw)


from pathlib import Path
import dotenv
import os

class _Loc:
    def __init__(self):
        self.root_folder = Path(__file__).parent.parent.parent
        self.temp_folder = self.root_folder/'temp'
        os.makedirs(self.temp_folder, exist_ok=True)
        env_file = self.root_folder/'environment.env'
        dotenv.load_dotenv(env_file)

Loc = _Loc()
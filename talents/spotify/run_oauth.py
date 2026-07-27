from talents.spotify.auth_server import AuthServer
from foundation_kaia.misc import Loc
from pathlib import Path
import dotenv
import os

if __name__ == '__main__':
    dotenv.load_dotenv(Loc.root_folder/'environment.env')
    AuthServer.run_authorization(
        os.environ['SPOTIFY_CLIENT_ID'],
        os.environ['SPOTIFY_SECRET_ID'],
        Path.home() / 'spotify_service.json',
        open_browser=False,
        port=9097
    )

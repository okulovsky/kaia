from talents.spotify.tools.auth_server import AuthServer
from foundation_kaia.misc import Loc
import dotenv
import os

if __name__ == '__main__':
    dotenv.load_dotenv(Loc.root_folder/'environment.env')
    AuthServer.run_authorization(
        os.environ['SPOTIFY_SERVICE_CLIENT_ID'],
        os.environ['SPOTIFY_SERVICE_SECRET_ID'],
        Loc.temp_folder / 'spotify_service.json',
        open_browser=False
    )

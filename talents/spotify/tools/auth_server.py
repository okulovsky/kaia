import requests
from flask import Flask, request
from yo_fluq import *
import time
from foundation_kaia.marshalling import ApiUtils
from foundation_kaia.fork import Fork
import urllib
import webbrowser
import os
from pathlib import Path

class AuthServer:
    def __init__(self, client_id: str, client_server: str, port: int, file_location):
        self.client_id = client_id
        self.client_server = client_server
        self.port = port
        self.redirect_uri = f'http://127.0.0.1:{self.port}'
        self.scopes = "user-read-playback-state user-modify-playback-state user-read-email streaming"
        self.file_location = file_location

    def __call__(self):
        app = Flask("SpotifyOAuthServer")
        app.add_url_rule('/heartbeat', view_func=self.index, methods=['GET'])
        app.add_url_rule('/', view_func=self.spotify, methods=['GET'])
        app.run('0.0.0.0', self.port)

    def index(self):
        return 'OK'

    def spotify(self):
        code = request.args.get("code")
        token_url = "https://accounts.spotify.com/api/token"
        response = requests.post(token_url, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_server
        })
        data = response.json()
        FileIO.write_json(data, self.file_location)

        return "OK"


    @staticmethod
    def run_authorization(client_id, client_secret, oauth_path, port=9097, open_browser: bool = True):
        if Path(oauth_path).is_file():
            os.unlink(oauth_path)

        server = AuthServer(client_id, client_secret, port, oauth_path)

        fork = Fork(server)
        fork.start()
        ApiUtils.wait_for_reply(f'http://127.0.0.1:{server.port}/heartbeat', 2, 'Spotify OAuth server')
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": server.redirect_uri,
            "scope": server.scopes
        }
        auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
        if open_browser:
            webbrowser.open(auth_url)
        else:
            print(auth_url)
        while True:
            if oauth_path.is_file():
                time.sleep(0.1)
                break
            time.sleep(0.1)
        fork.terminate()



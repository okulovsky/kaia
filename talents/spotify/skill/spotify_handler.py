from yo_fluq import FileIO
import requests
import base64
from pathlib import Path

from dataclasses import dataclass
import random

@dataclass
class Playlist:
    name: str
    uri: str

class SpotifyHandler:
    def __init__(self, client_id, client_secret, oauth_path, playback_device_name):
        self.oauth_path = Path(oauth_path)
        self.playback_device_name = playback_device_name
        self.device_id: str|None = None
        self.client_id = client_id
        self.client_secret = client_secret

    def _read_token(self):
        return FileIO.read_json(self.oauth_path)['access_token']

    def _is_token_expired(self) -> bool:
        access_token = self._read_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        if response.status_code == 401:
            return True
        return False


    def _refresh_token(self):
        oauth_data = FileIO.read_json(self.oauth_path)
        refresh_token = oauth_data.get("refresh_token")

        token_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()

        oauth_data["access_token"] = token_data["access_token"]
        FileIO.write_json(oauth_data, self.oauth_path)

    def _get_access_token(self):
        if self._is_token_expired():
            self._refresh_token()
        return self._read_token()

    def search_track(self, query, limit=5):
        url = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }
        params = {
            "q": query,
            "type": "track",
            "limit": limit
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        tracks = data.get("tracks", {}).get("items", [])
        if not tracks:
            print("No tracks found.")
            return

        result = []
        for i, track in enumerate(tracks):
            name = track["name"]
            artist = ", ".join(artist["name"] for artist in track["artists"])
            uri = track["uri"]
            track_id = track["id"]
            result.append(dict(
                caption = f'{name} ({artist})',
                uri = uri,
                track_id = track_id
            ))
        return result


    def _get_device_id(self):
        if self.device_id is None:
            url = "https://api.spotify.com/v1/me/player/devices"
            headers = {
                "Authorization": f"Bearer {self._get_access_token()}"
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            devices = response.json().get("devices", [])

            for device in devices:
                if device["name"].lower() == self.playback_device_name.lower():
                    self.device_id = device["id"]
            if self.device_id is None:
                raise Exception(f"Device '{self.playback_device_name}' not found. Available: {[d['name'] for d in devices]}")
        return self.device_id


    def play_track(self, track_uri):
        url = f"https://api.spotify.com/v1/me/player/play?device_id={self._get_device_id()}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }
        data = {
            "uris": [track_uri]
        }

        response = requests.put(url, headers=headers, json=data)
        if response.status_code != 204:
            raise ValueError("Failed to start track")


    def get_playlists(self, user_id: str = None, limit: int = 50) -> list[Playlist]:
        if user_id:
            url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        else:
            url = "https://api.spotify.com/v1/me/playlists"

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        playlists = []
        offset = 0

        while True:
            params = {"limit": limit, "offset": offset}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to get playlists: {response.status_code} - {response.text}")

            data = response.json()
            items = data.get("items", [])
            playlists.extend(Playlist(p["name"], p["uri"]) for p in items)
            if data.get("next") is None:
                break
            offset += limit

        return playlists

    def play_playlist(self, playlist_uri: str):
        device_id = self._get_device_id()
        access_token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # 1. Get playlist tracks
        playlist_id = playlist_uri.split(":")[-1]
        track_uris = []
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        params = {"fields": "items(track(uri)),next", "limit": 100}

        while url:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch playlist tracks: {response.status_code} - {response.text}")
            data = response.json()
            track_uris.extend([item["track"]["uri"] for item in data["items"] if item["track"]])
            url = data.get("next")
            params = None  # only needed on first request

        if not track_uris:
            raise Exception("Playlist is empty or unavailable.")

        # 2. Shuffle tracks
        random.shuffle(track_uris)

        # 3. Start playback with shuffled URIs
        play_url = f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
        json_data = {
            "uris": track_uris
        }

        response = requests.put(play_url, headers=headers, json=json_data)
        if response.status_code != 204:
            raise Exception(f"Failed to play playlist: {response.status_code} - {response.text}")


    def _send_command_request(self, method: str, endpoint: str, expected_code: int = 204):
        url = f"https://api.spotify.com/v1/me/player/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        response = requests.request(method, url, headers=headers)
        if response.status_code != expected_code:
            raise Exception(f"Spotify API error: {response.status_code} - {response.text}")

    def pause(self):
        self._send_command_request("PUT", "pause")

    def resume(self):
        self._send_command_request("PUT", "play")

    def next(self):
        self._send_command_request("POST", "next")

    def previous(self):
        self._send_command_request("POST", "previous")


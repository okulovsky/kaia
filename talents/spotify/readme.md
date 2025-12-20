To make it work, two parts are essential. The first is installing the software that 
actually plays music. This software is complex, so we don't want to rewrite it.
Official Spotify app should do the job for Android devices, 
but for Linux, additional work is needed. After this, you will have 
your console/tablet in the list of your devices. 

The second part is registering Kaia as a software that controls what and _where_
(including console) the Spotify will be playing this.

# Sound reproduction part

## spotifyd For Linux console:

Assuming you have:
* Main machine, the one where you sit comfortably with the keyboard and browser
* Console machine, which is running on Linux accessible with ssh

### Installing spotify
On the main machine, install `spotifyd`: 
  * `wget` from https://github.com/Spotifyd/spotifyd/releases/tag/v0.4.1
  * `tar -xvzf <filename>.tar.gz`
  * `chmod +x spotifyd`
  * `sudo mv spotifyd /usr/local/bin/spotifyd`

Repeat the same on the console (the package file may be different because of the architecture)

#### Building from source

Especially if spotify updated their protocol and release didn't catch up.

```
sudo apt update
sudo apt install -y build-essential pkg-config libasound2-dev libssl-dev libpulse-dev libdbus-1-dev git
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
rustc --version
cargo --version
```

Then pull the version of repo and compile:

```
git clone https://github.com/Spotifyd/spotifyd.git
cd spotifyd
cargo build --release
ls target/release/spotifyd
```

### Authenticate 

On the main machine:
* run `spotifyd authenticate`
* complete the procedure
* copy file `~/.cache/spotifyd/oauth/credentials.json` to the console

### Configuring and testing

On the console, create a config file (e.g., ~/.config/spotifyd/spotifyd.conf):
```
[global]
backend = "pulseaudio"
device_name = "KaiaConsole"
use_mpris = false
```

On the remote machine, run `spotifyd --no-daemon`

Perform test:
* Log in at main machine to `open.spotify.com`, choose track and start playing
* In the bottom-right corned, click on "Connect to device"
* You should see `KaiaConsole` as the available devide
* When clicking on it, the music will play at the console

### Running as a service

* mkdir -p ~/.config/systemd/user
* nano ~/.config/systemd/user/spotifyd.service

Paste:

```
[Unit]
Description=Spotifyd
After=network.target sound.target

[Service]
ExecStart=/usr/bin/local/spotifyd --no-daemon
Restart=always

[Install]
WantedBy=default.target
```

Then:
```
systemctl --user daemon-reload
systemctl --user enable spotifyd
systemctl --user start spotifyd
```

To view the logs:

```
journalctl --user -u spotifyd -f
```

To autostart:
```
sudo loginctl enable-linger $USER
```

# Control part

You also need to create your own application to _control_ the sound flow. To do this:

* Go https://developer.spotify.com/dashboard and accept the terms
* Create and app with 
  * Redirect URIs: `http://127.0.0.1:9097` (**not** localhost)
  * WebAPI, Web Playback SDK
* Store the client id and secret id in environmental variables

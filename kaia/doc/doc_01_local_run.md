# Running Kaia locally

## Docker

You need [Docker](https://docs.docker.com/engine/install/) installed in your system,
and the access granted to the current user to run `docker` from command line without elevated privileges.
The command

```commandline
docker run hello-world
```

should work successfully and produce the text starting with "Hello from Docker!"

## Node.js

The project has TypeScript source files for frontend, that needs to be compiled. To do so, Node.js must be installed:

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

```
source ~/.bashrc
```

```
nvm install --lts
```

## Python environment

[Anaconda](https://www.anaconda.com/download/success) is recommended to manage Python's
environments. Create an environment for e.g. Python 3.12 (BrainBox is tested with 3.10-3.13 Python versions):

```commandline
conda create --name kaia python==3.11
```

Then, activate the environment

```commandline
conda activate kaia
```

## Installing and running Kaia

From the **root directory of the repository** (not from `/kaia` directory), execute:

```
pip install -e .
```

Then, run Kaia by:

```
python -m kaia.run
```

It should produce the following output:

* Lots of lines starting with "Binding": that happens during composing the Kaia application
* "Starting supporting services": that means the four components of the application are starting as subprocesses:
  * `BrainBox` for managing the AI
  * `AvatarServer`, a main application bus
  * `AvatarDaemon`, a middleware that does most of the conversions from the primitives like text into sounds and vice versa
  * `KaiaDriver`, a backend that runs all the skills
* "Starting server on http://127.0.0.1:8090": BrainBox and Avatar web servers are running at the respective addresses.
* "Settings up BrainBox at http://127.0.0.1:8090".
This is where all the AIs, required by Kaia, will be built as containers, self-tested and inistantiated at your machine.
At the very first run, this step will take **a lot** of time and bandwidth.
However, that happens only at the first time you run Kaia.
* Then, the normal process will start and it will be represented by log lines in loguru format.

At this point, the webbrowser will be opened. You should see the loading screen, and then the main interface will appear.
You will need to give the web-page permissions to use the microphone, the web-camera and to play sounds without user's request.

Then, you will need to configure the microphone. Press the cog button in the bottom-left of the screen,
select "MicDebugView", and the following dashboard will appear:

Try speaking to a microphone. You should see the clear spike in the purple bars.
Then, you need to click the buttons on top of the dashboard, adjusting the dashed red line.
When you don't speak, the purple levels should be slightly lower than the line.
When you speak, the levels should be clearly above the line.
The picture shows the correct placement of the line.

Close the panel by clicking the cog button again.

Say "computer". You should hear a beep, that means, the assistant is ready for input.
If you don't hear it, try say it louder and/or clearer, avoiding heavy accent.
After the beep, say "What can you do?". You should hear another beep, and then the computer should respond
with the voice confirmation and the chat message that shows the available commands.


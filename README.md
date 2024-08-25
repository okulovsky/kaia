# Description

Kaia (Kitchen AI-Assistant) is an open-source home assistant with AI-generated voice, face and personality. 
It employes state-of-the-art free models to generate content and personalize home assistant. 


# Quick start

To run demo, the following external software is needed:

* [Docker](http://docker.com) to manage containers. 
  * On Windows, Docker Desktop app must run while demo is working. 
  * On Linux, it must run with current user's priviliges.
* [FFMPEG](http://ffmpeg.org) to manage sound files.
  * On Windows, it must be accessible from command line with `ffmpeg`.
* [PyAudio](https://pypi.org/project/PyAudio/).
  * On Windows, no steps are required.
  * On Linux, `sudo apt install python3-pyaudio`

Then, you need to install [Anaconda](https://www.anaconda.com/) to manage the dependencies.

## Creating the environment

* Open Console in Linux or Anaconda Terminal in Windows

* execute `conda create --name kaia python=3.11 -y`. 
  * This will create an environment with Python 3.11. 

* execute `conda activate kaia`
  * This will activate the created environment 

* change working dir to the root of the repository

* execute `pip install -e .`

If something went wrong during the installation or afterwards, reinstall the environment:

* execute `conda deactivate`, if the environment is activated.

* execute `conda remove --name kaia --all -y`

* repeat steps to create the environment

## Running a demo

Run `python demos/kaia/run_demo.py`. No GPU is required for this.

For the first time, it will take __a lot__ of time, as 3 containers will need to be downloaded/built.

If everything works, you will see several warnings
"WARNING: This is a development server. Do not use it in a production deployment."
After this, "Hello, nice to see you" is probably going to be said. 

At this point, you may open `localhost:8890` in your web-browser. 
To talk with Kaia, say wake word `computer`, wait for confirmation sound, 
and utter the command, e.g. "What can you do?"

### Troubleshooting

If you hear "Hello, nice to see you", but the system doesn't hear you, you would need to adjust your input settings.
They are located in `demos/kaia/audio_control.py`, method `create_release_control_settings`.

If you say "computer" and then __do not__ hear a confirmation sound:
check `mic_device_index`, by default it is set -1, which is default mic.
Try to change the value, or physically find your system default mic and speak into it.
Restart the app.
 
If you hear confirmation after "computer", but not after the command you say:
you probably need to adjust your silence levels. 
Go to 127.0.0.1:12111/graph - it draws a graph of everything you say in the mic within last couple of seconds.
Find a value that clearly separates silence from signal, and put it in `silence_level` argument.
Restart the app.

If you hear both confirmation signals, but the command is consistantly misrecognized:
Go to 121.0.0.1:8090 , this is BrainBox console. Find a job belonging to Rhasspy with ID like 
`<ID>.rhasspy`.
Then get the file `121.0.0.1:8090/file/<ID>.input.wav` and listen to this. 
If you hear too high/too low pitch, wrong `sample_rate` is the reason. 
Find out which sample rate your OS runs the mic, update the settings and restart the app.
 

## Browsing the documentation

My experience with research project shows that the best way to provide a documentation for the research project
is with Jupyter notebooks. These notebooks explain different subsystems of `Kaia`, and also you can play with
them around, if you're curious how this and that functionality works. I try to update the notebooks along with
the releases, but it might be imperfect.

To view the notebooks:

* execute `jupyter lab` in console with activated `kaia` environment

* do not close the console.

A browser will open and you will see the contents of the root of the repostiory. 
Open `demos` folder, then `Part 00 - Intro.ipynb`. Follow the instructions in this file.


# Description

Kaia (Kitchen AI-Assistant) is an open-source home assistant with AI-generated voice, face and personality. 
It employes state-of-the-art free models to generate content and personalize home assistant. 

**The project is currently underconstruction**. 
There is a stable part of the project, `BrainBox`, that is located in `/brainbox` 
and has its own documentation and even Pypi-release.
The voice assistant itself currently runs either on a normal computer or on a custom RaspberryPi device. 
We are taking the steps to enable Kaia's frontent running on Android- and IOS-devices. 
Once that happens, you will be able to enjoy the project at your home!  


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

## Installing deciders

Run `python kaia/demo/install.py`.

This will build three AI systems that are required for the demo: 
text-to-speech (OpenTTS) and two speech-to-text (Kaldi and Whisper),
and also will download all the base models required.

It takes a lot of time and traffic, so be patient.

The script will also self-test these containers. 
The HTML-reports about the self-testing will be located `data/brainbox_self_test/`

## Running Kaia

Run `python demos/kaia/run_demo.py`. No GPU is required for this.

If everything is fine, you will see several warnings
"WARNING: This is a development server. Do not use it in a production deployment.".
Then, messages of shape "[Processing item] TimerTick(current_time=datetime.datetime(...))"
will start appearing continuously.

After that, you may open at this point, you may open `localhost:8890` in your web-browser.
There should be a nice AI-generated image, and the text "Hello, nice to see you" in the chat control on the right.
This sentence should also be said.

To talk with Kaia, say wake word `computer`, wait for confirmation sound, 
and utter the command, e.g. "What can you do?". After this, another confirmation sound
should be emitted. 

You may use the command "Computer! What can you do?" to get the list of available commands.

### Troubleshooting

If you hear "Hello, nice to see you", but the system doesn't hear you, you would need to adjust your input settings.
They are located in `kaia/demo/run_demo.py`.

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
 

# Description

`kaia` is an open-source home assistant with AI-generated voice, face and personality. 
It employes state-of-the-art free models to generate content and personalize home assistant. 


# Quick start

To run demo, the following external software is needed:

* [Docker](http://docker.com) to manage containers. 
On Windows, it must run while demo is working. 
On Linux, it must run with current user's priviliges.
* [FFMPEG](http://ffmpeg.org) to manage sound files.
On Windows, it must be accessible from command line with `ffmpeg`.
* [PyAudio](https://pypi.org/project/PyAudio/). 
On Windows, no steps are required.
On Linux, `sudo apt install python3-pyaudio`

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

Run `python my/demo/run_demo.py`. No GPU is required for this.

For the first time, it will take __a lot__ of time, as 3 containers will need to be downloaded/built.

If everything works, you will see several warnings
"WARNING: This is a development server. Do not use it in a production deployment."
After this, "Hello, nice to see you" is probably going to be said. 

At this point, you may open `localhost:8890` in your web-browser. 
To talk with Kaia, say wake word `computer`, wait for confirmation sound, 
and utter the command, e.g. "What can you do?"

It may not work out of the box, because you may need to additionally configure your audio system. 
At the moment, it can only be done via the code in `my/demo/audio_control.py`
* `mic_device_index` set to -1 means default mic. Configure your system if it's not the expected mic.
* `sample_rate` is a parameter of your mic. 
To be fair, I have no idea how to detect it. If something doesn't work, try using 44100 and 48000 values.
* `silence_level` is a value used to tell voice and silence apart. To retrieve it:
  * run `python my/demo/audio_test.py`
  * Say "computer" several times. 
  * Each time, the levels of the last frames are produced, get the border somewhere between first and last.

## Browsing the documentation

My experience with research project shows that the best way to provide a documentation for the research project
is with Jupyter notebooks. These notebooks explain different subsystems of `Kaia`, and also you can play with
them around, if you're curious how this and that functionality works. I try to update the notebooks along with
the releases, but it might be imperfect.

To view the notebooks:

* execute `jupyter notebook` in console with activated `kaia` environment

* do not close the console.

A browser will open and you will see the contents of the root of the repostiory. 
Open `demos` folder, then `Part 00 - Intro.ipynb`. Follow the instructions in this file.


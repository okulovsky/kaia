# Description

`kaia` is an open-source home assistant with AI-generated voice, face and personality. 
It employes state-of-the-art free models to generate content and personalize home assistant. 


# Quick start

First, you need to install [Anaconda](https://www.anaconda.com/) to manage the dependencies.

## Creating the environment

* Open Console in Linux or Anaconda Terminal in Windows

* execute `conda create --name kaia python=3.11 -y`. 
  * This will create an environment with Python 3.11. 

* execute `conda activate kaia`
  * This will activate the created environment 

* change working dir to the root of the repository

* execute `pip install -e .`

* execute `jupyter notebook`

* do not close the console.

At this point, a browser will open and you will see the contents of the root of the repostiory. 
Open `demos` folder, then `Part 00 - Intro.ipynb`. Follow the instructions in this file.

### If you messed up...

It's allright, here is how to fix it:

* Press Ctrl-C two times in the terminal where the notebook server is running. 

* execute `conda deactivate`

* execute `conda remove --name kaia --all -y`

* repeat "Creating the environment section"


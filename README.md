# Description

`kaia` is an open-source home assistant with AI-generated voice, face and personality. 
It employes state-of-the-art free models to generate content and personalize home assistant. 


# Quick start

First, you need to install [Anaconda](https://www.anaconda.com/) to manage the dependencies.

## Creating the environemnt

* Open Console in Linux or Anaconda Terminal in Windows

* execute `conda create --name kaia python=3.8 -y`. 
  * This will create an environment with Python 3.8. An old one, but this is what the library was tested with. 

* execute `conda activate kaia`
  * This will activate the created environment 

* change working dir to the root of the repository

* execute `pip install -r requirements.kaia.txt`
  * This will install to the environment the exact versions of the libraries that Kaia was tested with.
  * ML projects inside Kaia might have different requirements. It will be discussed in their notebooks.

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


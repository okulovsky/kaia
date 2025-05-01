# Voice clone

This process will help you to create a Piper model than speaks with the voice of your character of any language.

The process is:

* Prepare ~30 sec of **samples** that you will take from the original source
* Prepare ~2000 **sentences** that will well represent the desired language
* Pick the right **voice_cloner** for the task, deciding on the technology used (Zonos, XTTS, etc)
* Run the **upsampling** and convert 30 sec of samples to 60-90 minutes of training data
* Run the **training** and create a Piper model.

Each of the corresponding folders contains a notebook that has the main skeleton of the code you need to use,
as well as some experience on how to do these things properly.
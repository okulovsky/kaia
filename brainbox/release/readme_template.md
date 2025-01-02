# Introduction

BrainBox provides easy HTTP access to a set of curated Docker containers 
with AI-systems processing images, texts and sounds.
It comes with API endpoints to build the container and download basic models, 
self-tests and documentation, as well as unified access to all the models.
The main use case is fast prototyping of small AI-driven products: 
managing chats in messengers, self-hosted voice assistants, 
media processing (translation, covering images), etc.
BrainBox is open-source and self-hosted, so no external APIs are needed; 
GPU is recommended for some, but not all, models.

BrainBox is not a production-ready solution. **Do not use it** in production environment,
since it doesn't have any security features, isn't really compatible with high and even 
moderate load, and at the same time may have a big impact on the system's resources. 
The suggested use of BrainBox is your own home machine, 
where the security is provided on the network, not application, level.
Ideally, this machine would have a decent GPU unit: many AI-systems do not require GPU,
but some (the most interesting ones, of course) are practically useless without it,
and few won't even run.

## Included deciders

They are many. 
At some point, BrainBox will have a comprehensive documentation for each of them, but we're not there yet.
Important deciders are:
* For TTS, text-to-speech: 
  * [OpenTTS](https://github.com/synesthesiam/opentts) provides a decent baseline for english language with VITS model
  * [CoquiTTS](https://github.com/coqui-ai/TTS) is a framework supporting many different models.
    That includes VITS as well as YourTTS, and, of course, their own XTTS, that can do a good voice cloning.
  * [TortoiseTTS](https://github.com/neonbjb/tortoise-tts) is, in my opinion, still the best in terms of quality. 
    It is very slow, but not as slow as it used to be. 
* For STT, speech-to-text, and other voice analysis:
  * [Whisper](https://github.com/WhisperSpeech/WhisperSpeech) is a de-facto standard.
  * [Kaldi](https://kaldi-asr.org/), which we use via its implementation in [Rhasspy](https://rhasspy.readthedocs.io/en/latest/),
    provides much faster and accurate result _over the closed grammar and vocabulary_. 
    It is not really a general solution for STT, but is perfect for home assistants.
  * [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) does speaker identification.
* For text processing:
  * [Ollama](https://ollama.com/), a de-facto standard for LLM management, is supported.
* For image generation and processing:
  * [ComfyUI](https://github.com/comfyanonymous/ComfyUI), a standard for image generation, is supported
  * [YOLO](https://docs.ultralytics.com/) is supported for object detection.

... And more are coming. 
Once you install BrainBox, you will have all these AIs privately and free of charge on your machine, 
accessible via user-friendly Python API, or by simple HTTP requests!    
 
# Installation

## Docker 

You need [Docker](https://docs.docker.com/engine/install/) installed in your system, 
and the access granted to the current user to run `docker` from command line without elevated privileges.
The command

```commandline
docker run hello-world
```

should work successfully and produce the text starting with "Hello from Docker!" 

## Python environment

[Anaconda](https://www.anaconda.com/download/success) is recommended to manage Python's 
environments. Create an environment for e.g. Python 3.11 (BrainBox is tested with 3.10-3.13 Python versions):

```commandline
conda create --name brainbox python==3.11
```

Then, activate the environment

```commandline
conda activate brainbox
```

## BrainBox

Install the brainbox

```commandline
pip install kaia-brainbox
```

Run the brainbox

```commandline
python -m brainbox.run --data-folder <where_all_files_will_be_stored>
```

You should see something like:
```
 * Serving Flask app 'RPC_BrainBoxService'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8090
```

Please check the Troubleshooting session if instead you see something like this:
```
 * Serving Flask app 'RPC_BrainBoxService'
 * Debug mode: off
Address already in use
Port 8090 is in use by another program. Either identify and stop that program, or start the server with a different port.
```

Run the build-in test. It will make sure that all the functions, mentioned in this README, work correctly

```python
python -m brainbox.run_test
```

If you see `ALL GOOD` in the end, it means BrainBox is installed and ready.

## Troubleshooting

If the port is busy:
* Maybe the port `8090` assigned to other application in your system. In this case, use `--port` argument to both
  `brainbox.run` and `brainbox.run_test` commands.
* Maybe you try to run the second instance of the BrainBox on the same port. Don't do it.
* Maybe you were running BrainBox before and shut it down incorrectly. 
  In this case, check your processes and kill those from `python`.
  Or simply restart the machine.

<<<FROM_TESTS>>>





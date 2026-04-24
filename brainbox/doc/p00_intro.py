"""
# Introduction

BrainBox provides easy HTTP access to a set of curated Docker containers
with AI-systems that process images, texts and sounds.
It comes with API endpoints to build the container, download basic models,
perform self-tests, as well as unified access to all the models and documentation.
The main use case is fast prototyping of small AI-driven products:
managing chats in messengers, self-hosted voice assistants,
media processing (translation, covering images), etc.
BrainBox can also serve as a bridge between your non-Python application, be it front- or backend,
and the pythonic world of AIs: the HTTP calls have the predictable format
and can be performed from any programming language.
For Python, the elegant and easy-to-use API is provided.

BrainBox is open-source and self-hosted, no external APIs are needed.
All the data are processed on your device.

The suggested use of BrainBox is your own home machine or the remote server accessible via VPN.
BrainBox doesn't have any security features, so the access control must be provided on the network, not application, level.
Ideally, this machine would have a decent GPU unit: many AI-systems do not require GPU,
but some (the most interesting ones, of course) are practically useless without it,
and few won't even run.

## Included deciders

There are many! Once you install BrainBox, you will have all these AIs privately and free of charge on your machine,
accessible via user-friendly Python API, or by simple HTTP requests.

### Text-to-speech

Best choice:
* [Piper](https://github.com/rhasspy/piper) - fast and resource-efficient text-to-speech.
Lots of languages are supported.
* [CosyVoice](https://github.com/Zyphra/Zonos) - ultimate solution for artistic, multilingual voice-cloning.
Perfect results in terms of quality and stability.
* PiperTraining: a container to train models for Piper.

### Speech-to-text and voice analysis

* [Whisper](https://github.com/WhisperSpeech/WhisperSpeech) is a de-facto standard.
* [Kaldi](https://kaldi-asr.org/), which we use via its implementation in [Rhasspy](https://rhasspy.readthedocs.io/en/latest/),
  provides much faster and accurate result _over the closed grammar and vocabulary_.
  It is not really a general solution for STT, but is perfect for home assistants.
* [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) does speaker identification.
* [Vosk](https://alphacephei.com/vosk/) - can be faster than Whisper,
also the results have more direct connection to the audio, e.g. each word is located to timestamps.

### LLM and text processing

* [Ollama](https://ollama.com/), a de-facto standard for LLM management, is supported.
* [EspeakPhonemizer](https://pypi.org/project/espeak-phonemizer/) converts text to phonemes for many languages.
Mainly here because of how troublesome it is to install it on Windows.

### Image generation and processing
* [YOLO](https://docs.ultralytics.com/) is used for fast object detection with neural netowrks.
* [WD14Tagger](https://github.com/corkborg/wd14-tagger-standalone) describes the images with the tags.
Also available in ComfyUI, but has some additional perks.
* VideoToImages converts video to a series on images, allowing to select most sharp frame and to skip similar frames.

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
environments. Create an environment for e.g. Python 3.12 (BrainBox is tested with 3.10-3.13 Python versions):

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
Starting server on http://127.0.0.1:8090
```

If you see:
```
ERROR:    [Errno 98] error while attempting to bind on address ('0.0.0.0', 8090): [errno 98] address already in use
```
consult the Troubleshooting section.

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

"""
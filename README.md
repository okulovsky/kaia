# Description

Kaia (Kitchen AI-Assistant) is an open-source, local-first 
home assistant with AI-generated voice, face and personality.

Kaia **is not** a gateway from a tablet to the paid AI in the cloud. 
We believe the kitchen conversations should stay in the kitchen, and therefore only employ open-source, 
self-hosted models in this project, so the assistant is completely private.
We also believe that using a GPU machine 24/7 to power the kitchen assistant is extravagancy, 
so all the AI in Kaia can be run on a decent laptop without GPU
(however, the procedures to train or distill these AIs cannot).
That for sure presents certain challenges, but is also a good example of a rational use of computational resources,
as well as a demonstration of how much could actually be done in this setup.

Kaia is designed to be more a toolbox than a product. 
It does not contain all the skills imaginable you may use out of the box, 
or a library of characters you can employ as your assistant. 
Instead, Kaia contains the tools to create such skills or characters.
This way, Kaia can be your companion in the world of AI,
where you can experiment with AI on your own, and immediately see the results right in your kitchen.

This monorepo contains multiple projects.

* `kaia` is the runnable kitchen assistant. 
It contains instructions on how to run the assistant on your machine or deploy it on the remote machine.
* `brainbox` is a module that hosts over 15 AIs in the docker container, enabling the access to them via API or HTTP. 
BrainBox is heavily used in Kaia, but can also employed in any pet project you want to create, isolating functionality
such as voiceover or speech recognition. 
It is very well documented and contains instructions on how to use brainbox both with Python API or with the raw HTTP requests
* `chara` is a collection of scripts that are used to train and personalize the kitchen assistant. 
Currently, there are scripts that allow you to clone the voice you choose and distill it as a small model that runs even on Raspberry Pi,
as well as the scripts to paraphrase the utterances of the kitchen assistant with custom personality of the character.
More are planned, e.g. training Kaia to recognize the family members by voice and face, create the characters' images
and their own universes with the daily schedules, or train an NLU to recognize your speech on different languages.
* `avatar` is a bridge that connects the world of AI with the frontend. It contains a webserver with a bus for messages
that encode all the inputs and outputs: voice commands and replies, text messages, images change and so on. 
It also contains middleware that employs `brainbox` to e.g. translate a text command emitted by Kaia into speech command.
A TypeScript library with the widgets that perform these commands, as well as emit events from microphone or camera, 
are also stored in `avatar`.
* `grammatron` is a small NLG utility that allows you to define templates to transform variables in the coherent and 
grammatically correct text. It supports English, Russian and German languages, but can be extended to other european 
languages as well, and maybe even beyond. 
* `eaglesong` is a small library that enables a natural way to write the conversations: instead of manually implementing
the state machine that advances on the user's input, you can write it naturally in the format "say this, listen, then say that",
and turn it in to state machine using Python generators mechanics. It is well documented.
* `foundation_kaia` contains the utilities that are used by other modules. 
The most important utility is `marshalling` that allows you to create a stereotypic FastAPI server and API
from properly decorated and annotated class. It is well documented.


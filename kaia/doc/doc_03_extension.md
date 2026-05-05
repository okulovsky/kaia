# Extending functionality

The simplest way to extend the functionality of Kaia is to simply write to the demo folder all the changes you need.
This is perfectly fine if you just want to play with the assistant and learn about its functionality.

However, this approach may expose your code, which may contain the sensitive data, on pushing.
If you do not want it, you may of course simply copy-paste the Kaia code to your repository,
but then you won't be able to update properly.

The correct and private way to do the extension is to install the repository and then create your own
private folder (e.g. in the private repository), that will tweak the `kaia/app` folder.
All classes there are written in such a style that allow easy extension:
e.g., skills are separated into "common skills" like time or date that we assume are helpful for any assistant instance,
and "specific skills" like cookbook, which we encourage the users to setup for their needs.

## Adding a new skill

To add a simple, one-line Kaia skill, where assistant provides an answer to the question, you generally need to:

* Define the template of intent or intents which will trigger the skill
* Define the template of reply to the skill
* Define the logic of the skill.

You can take an inspiration in:
* `PingSkill`: the simplest skill where the intent doesn't have any parameters.
* `DateSkill` or `TimerSkill`: the skill where there are the parameters in the intent
* `EchoSkill`: the simplest skill that demonstrates the free-form input and output, as well as a multi-line skill
* `CookbookSkill` is also a multi-liner, and it shows how to interact with time
* `walk_in_skill` demonstrates how to react not only to spoken commands, but also to the fact that the user become visible to the web cam.

After you've implemented the skill, it is usually a good idea to test it.
The skills are implemented with the `eaglesong` library that offers the convenient way of writing the tests
as the natural dialogs: say this to the assistant, then expect this as a reaction.
`grammatron` library that you will use to define the intents and replies, are designed to be compatible with
`eaglesong` testing procedures. You can, again, take the inspiration in the tests that are provided with the skills.

## Defining your own character

For the various reasons we do not provide the library of the characters, nor do we plan it anywhere in the future.
If you want to personalize your assistant, you have to do it yourself.

For that, you need:

* Voice clone the character
* Paraphrase all the replies of the assistant so they match the character personality
* Create the images of the character so you can see them living their lives in the assistant

For the first two tasks, there are working and tested pipelines in `chara` project that you can use.
For the third task, the pipeline is pending.

## Kaia in a household with multiple users

Kaia can detect a user by voice and by face. These pipelines require you to collect
some samples from the working devices, annotate them to indicate which image/sound file corresponds to whom,
and then upload samples to the server. There will be `chara` pipelines to do this, but at the current time
they are under construction.
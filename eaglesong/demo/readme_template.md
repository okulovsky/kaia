# eaglesong

Chat media, be it Telegram or almost anything else, usually organize the chat within a "per request" approach:
the chatbot is given the incoming message and must produce the result. 
However, in case of longer conversations, it is easier to code the process from the chatbot's point of view: 
say this, listen to human, parse the input, say something else. 
`eaglesong` provides exactly this possibility. You write chat flows like this:

```python
yield "First question"
first_answer = yield Listen()

yield "Second question"
second_answer = yield Listen()
```

and then control system builds a Telegram bot (or bot for other media) from such flows.

When a Telegram bot receives the very request for an update, it creates an iterator over main function, and pulls commands from it until it's Listen. At this point the request is considered complete, iterator is stored and the bot return the control to Telegram loop. On the second request, it will restore the iterator and continue with the updated context field from the exactly same point where it was interrupted.

Some people suggested yield approach can be replaced with async/await, keeping the logic of the conversation flow intact. Some other people, however, offered arguments why these approaches, although similar and based on the same design pattern, are not equivalent in Python and hence async/await cannot be used in this particular case.

* Unfortunately, my understanding of async/await does not allow me to answer this question with certainty. If someone wants to reimplement eaglesong with async/await, this and further demos provide a good understanding of the use cases that need to be considered.
* In general, I don't believe writing await instead of yield will improve anything. Although, we could benefit from some standard await management from asyncio.
* Both approaches should be able to coexist side-by-side with Automaton class abstraction.
* `aiogram` seems to implement this approach for Telegram; however, it seems like using this approach in Kaia would bring `async/await` everywhere inside it, which is not my wish.

There are a few demos demonstrating the different designs of the chatflow with eaglesong, located in `demo` subfolder. 
They are all runnable and you should be able to run a Telegram bot with each of them.
Before running the bots from demos/eaglesong, you will need:
* Contact `@BotFather` bot on Telegram and register your chatbot. As the result, you will obtain an API key that looks like this: 0000000000:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
* Create an environment.env file in the repository's root. This file is already in .gitignore, so don't be afraid to accidentaly push its contents.
* Place KAIA_TEST_BOT=<YOUR_API_KEY> in the environment.env file.

After that, simply run each file and enjoy the bot.

If you don't wish to do it, the Appendix to this readme will contain the source code of the examples with the explanations.

`eaglesong` also offer elegant method to test the conversation flows, written in this fashion. To see how, consult `tests/test_demo/` folder.

# eaglesong.templates

Templates are the way to define the utterances of the chatbot __or__ the user, 
and convert them into text, or parse from texts. 

The template can be defined like this:

```python
from eaglesong.templates import TemplateVariable, Template, CardinalDub

DURATION = TemplateVariable("duration", CardinalDub(0,100))
template = Template(f"Set the timer for {DURATION} minutes")

utterance = template(20)

utterance.to_str() #produces "Set the timer for twenty minutes"

template.parse("Set the timer for twenty minutes") #produces {'duration': 20}
```

Templates and utterances are very comfy to use in skill design and in tests writing,
they are well-integrated with `eaglesong` infrastructure. 
I also like the simple way to define the templates.

Templates additionally allow:
* to build a regexp for a string to parse
* to build a datastructure for Rhasspy INI-file that is converted to a graph and then fed to Kaldi for voice recognition

Templates are very useful, but they were one of the first subsystems designed for Kaia
and I'm not particularly proud of the way they are implemented. 

The biggest issue is an overenginered algorithm that builds regexps, ini-files and all that.
Essentially, template is defined as a regular expression without iteration 
(because iterations are not compatible with Kaldi),
and these algorithms are implemeted as subclasses of a generic `Walker` 
that walks depth-first over the regular expression. While effective, 
it's hard to read and modify, and I think there must be a better way to write it.

The second problem is globalization: the current implementation suggests
that for each language new `CardinalDub` (also DatetimeDub, etc) must be defined,
and also the whole new set of templates. It would be much better if Dubs accept
the language as an argument for to_str/parsing, and the Template would be defined like:

```python
Template(
    en=f"Set the timer for {DURATION} minutes",
    de=f"Stelle den Timer auf {DURATION} Minuten"
)
```

At some point, I hope to rework the templates completely to address
these issues.


# eaglesong demo

<<<FROM_DEMO>>>
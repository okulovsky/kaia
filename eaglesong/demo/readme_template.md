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

# eaglesong demo

<<<FROM_DEMO>>>
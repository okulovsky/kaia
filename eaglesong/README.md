# Table of contents

* [eaglesong](#eaglesong)
* [eaglesong demo](#eaglesong-demo)
  * [Echobot: Introduction](#echobot:-introduction)
  * [Questionnaire: Calling other functions](#questionnaire:-calling-other-functions)
  * [Authorization: combining chat flows](#authorization:-combining-chat-flows)
    * [No reusability: copy and paste!](#no-reusability:-copy-and-paste!)
    * [Reusability on the methods' level](#reusability-on-the-methods'-level)
    * [Implementing chat flow as a class](#implementing-chat-flow-as-a-class)
    * [Providing the chatflow as inner routine](#providing-the-chatflow-as-inner-routine)
  * [Example library](#example-library)
    * [Custom actions in menu](#custom-actions-in-menu)
  * [Writing Telegram-native skills](#writing-telegram-native-skills)
  * [Timers](#timers)
    * [Advanced timer's handling](#advanced-timer's-handling)

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



## Echobot: Introduction

The most important thing to remember is that every time you want your bot
to say or to do something, you have to type `yield`.

The same applies when you want your bot to listen: you type `yield Listen()`.

With this, the following code is pretty self-explainatory: say the welcome message,
and then listen to what the user says and then repeat to him.

Class `Bot`, imported from `eaglesong.demo.common` is specific for demos,
and incapsulates different ways of defining the bots. We will cover these ways
along the demo, right now it's simple: just bot over `main` function. `run` starts
this bot.

```python

from eaglesong.demo.common import *

def main():
    yield f'Say anything and I will repeat. Or /start to reset.'
    while True:
        input = yield Listen()
        yield input

bot = Bot("echobot", main)

if __name__ == '__main__':
    run(bot)

```

## Questionnaire: Calling other functions

How do we call other functions from `main`?

If it's just a normal Python function, such as `datetime.now()` below, you can of course
just call it and use the returned value normally.

But if this function represents chat flow, you need to use `yield from`.

Please note the difference between `yield Listen()` and `return name, country` in `questionnaire`.
`yield Listen()` kinda-return `Listen()` object, but this is not a true return, it doesn't terminate the function
execution. `return name, country` is a true return: it terminates the function and the value `(name, country)`
is assigned to the result of the whole `yield from questionnaire()` call
(and thus to `name, country` variables in `main` method).

```python

from eaglesong.demo.common import *
from datetime import datetime

def questionnaire():
    yield 'What is your name?'
    name = yield Listen()

    yield f'Where are you from, {name}?'
    country = yield Listen()

    return name, country

def main():
    name, country = yield from questionnaire()
    current_time = datetime.now()
    yield f"Nice to meet you, {name} from {country}! By the way, the current time is {current_time}"

bot = Bot("quest", main)

if __name__ == '__main__':
    run(bot)
```

## Authorization: combining chat flows

This section demonstrates how to achieve code reusability across different chatflow

### No reusability: copy and paste!

Authorization is very important step of the chat bot. The following code shows the simplest way
to authorize only yourself as a user of the chatbot: you just write your chat id in env. variable,
and check that the user is legit.

```python

from eaglesong.demo.common import *

def main():
    context = yield ContextRequest()
    user_id = context.user_id

    if 'KAIA_TEST_BOT_CHAT_ID' not in os.environ:
        raise Terminate(f'Please add CHAT_ID environment variable. Your id is {user_id}')
    allowed_user_id = int(os.environ['KAIA_TEST_BOT_CHAT_ID'])

    if user_id != allowed_user_id:
        raise Terminate(f'User {user_id} is not authorized')

    yield f'Say anything and I will repeat. Or /start to reset.'
    while True:
        input = yield Listen()
        yield input

bot = Bot("auth1", main)

if __name__ == '__main__':
    run(bot)
```

### Reusability on the methods' level

Now let's see how we can organize the authorization code better, to be able to reuse it.

First, we can decompose the code to `authorize` and `echobot` methods, and combine the calls in `main`.

```python
from eaglesong.demo.common import *
from eaglesong.demo.example_01_echobot import main as echobot

def authorize(env_variable):
    context = yield ContextRequest()
    user_id = context.user_id

    if env_variable not in os.environ:
        yield Terminate(f'Please add `{env_variable}` environment variable. Your id is {user_id}')
    allowed_user_id = int(os.environ[env_variable])

    if user_id != allowed_user_id:
        raise Terminate(f'User {user_id} is not authorized')

def main():
    yield from authorize('KAIA_TEST_BOT_CHAT_ID')
    yield from echobot()

bot = Bot("auth2", main)

if __name__ == '__main__':
    run(bot)

```

### Implementing chat flow as a class

The decomposition to functions is totally fine. But myself, I prefer the object-oriented way of encoding skills.
Here, we first create `Authorize` object. Then, we may do some fine-tuning of this object (sometimes
skills have lots of internal variables and it's unhandy to place all of them in constructor). And finally,
we use this object like a function in `yield from`.

Essentially, we write something like `yield from Authorize('KAIA_TEST_BOT_CHAT_ID')()`.
Those double brackets may seem weird, but this is totally fine thanks to `Authorize` class
implementing `__call__` method.

```python
from eaglesong.demo.common import *
from eaglesong.demo.example_01_echobot import main as echobot

class Authorize:
    def __init__(self, env_variable):
        self.env_variable = env_variable

    def __call__(self):
        context = yield ContextRequest()
        user_id = context.user_id

        if self.env_variable not in os.environ:
            yield Terminate(f'Please add `{self.env_variable}` environment variable. Your id is {user_id}')
        allowed_user_id = int(os.environ[self.env_variable])

        if user_id != allowed_user_id:
            raise Terminate(f'User {user_id} is not authorized')

def main():
    authorize = Authorize('KAIA_TEST_BOT_CHAT_ID')
    # Here some fine-tuning of `authorize` object can take place
    yield from authorize()
    yield from echobot()

bot = Bot("auth2", main)

if __name__ == '__main__':
    run(bot)

```

### Providing the chatflow as inner routine

Finally, let's get of this `main` method, so we could compose our skill from `Authorize` object and
`echobot` function like from bricks. To do so, we pass `echobot` function to `Authorize`, and
`Authorize` will call it when ready.

There is one non-trivial moment about this bot. In previous cases, we run `main` method, and inside
this method, created `Authorize` object (and potentially lots of other objects). For each new user of the chat bot,
its individual `main` call was created, and individual copies of all other objects.

**By default, it's not the case now**. If you create bot as in the commented line below, there will be one object
for all the users of the chatbot, and all of them will share its fields values!

Sometimes it's a desirable behaviour. But often enough we want to avoid it, use the `lambda` syntax as below.

```python
from eaglesong.demo.common import *
from eaglesong.demo.example_01_echobot import main as echobot

class Authorize:
    def __init__(self, env_variable, inner_routine):
        self.env_variable = env_variable
        self.inner_routine = inner_routine

    def __call__(self):
        context = yield ContextRequest()
        user_id = context.user_id

        if self.env_variable not in os.environ:
            yield Terminate(f'Please add `{self.env_variable}` environment variable. Your id is {user_id}')
        allowed_user_id = int(os.environ[self.env_variable])

        if user_id != allowed_user_id:
            raise Terminate(f'User {user_id} is not authorized')

        yield from self.inner_routine()

```

INCORRECT way to create a bot would be:
`bot = Bot("auth2", Authorize('KAIA_TEST_BOT_CHAT_ID', echobot))`

It can be fixed with deepcopy, but that is sometimes desired behaviour, so factory is better

The correct way is:

```python

bot = Bot("auth2", lambda: Authorize('KAIA_TEST_BOT_CHAT_ID', echobot)())

if __name__ == '__main__':
    run(bot)

```

## Example library

This will demonstrate a reusable `menu` component, handy for different Telegram chatbots

The following menu allows you to pick a value from the lists. The value is then displayed to you.

```python
from eaglesong.demo.common import *
from eaglesong.drivers.telegram.menu import *

def create_menu():
    menu = MainMenu(
        MenuFolder("Choose the question").items(
            MenuFolder("Where do you live?").items(
                ValueMenuItem("Europe"),
                ValueMenuItem("Asia"),
                ValueMenuItem("Other")
            ),
            MenuFolder("How old are you?").items(
                ValueMenuItem("<18"),
                ValueMenuItem("18-30"),
                ValueMenuItem("30-40"),
                ValueMenuItem(">40")
            )
        )
    )
    return menu

def main():
    result = yield from create_menu()()
    yield f"You have selected: {result}"

bot = Bot("menu1", main)

if __name__ == '__main__':
    run(bot)

```

### Custom actions in menu

You can also associate custom actions with menu items.

The first way is to create a class inherited from `MenuItem`, and implement it's `run` method.

Alternatively, you can just write the Routine in the function and create `FunctionalMenuItem` in it.

```python

from eaglesong.demo.common import *
from eaglesong.drivers.telegram import menu
import requests

class WeatherMenu(menu.MenuItem):
    def __init__(self, city, lat, long):
        self.city = city
        self.lat = lat
        self.long = long

    def run(self):
        response = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.long}&current_weather=true')
        temp = response.json()['current_weather']['temperature']
        yield f"Temperature in {self.city}: {temp}"

    def get_caption(self):
        return self.city

def say_nice_thing():
    yield "You are handsome!"

def say_naugty_thing():
    yield "I'm horny!"

def create_menu():
    main = (
        menu.MenuFolder('Select an option').items(
            menu.MenuFolder('Weather').items(
                WeatherMenu("Yekaterinburg",56.83, 60.58),
                WeatherMenu("Berlin",52.52,13.40)
            ),
            menu.MenuFolder('Small talk').items(
                menu.FunctionalMenuItem('Nice', say_nice_thing),
                menu.FunctionalMenuItem('Naughty', say_naugty_thing, terminates_menu=False)
            ),
            menu.MenuFolder(lambda: str(datetime.now()), 'Time', True)
        )
    )
    return main

def main():
    yield f'Hi! Say anything and I will repeat. Or open /menu'
    while True:
        input_text = yield Listen()
        if input_text == '/menu':
            yield from create_menu()()
            continue
        yield input_text

bot = Bot("menu", main)

if __name__ == '__main__':
    run(bot)
```

## Writing Telegram-native skills

`eaglesong` allows you to write the skills for Telegram only,
without using TelegramTranslationFilter.

In this case, `TgContext` will be your context (containing Telegram primitives
of the input), and the output will be TgCommand. To create TgCommand with
hints from IDE, use TgCommand.mock().

This is fine approach, if you really want to create a Telegram skill (e.g. one managing Telegram group).
But if you program a generic skill, it is better not to use this approach, as it's better to keep the skill
compatible with other media (such as voice assistant). Also, Telegram skills are a bit more cumbersome to
write and to test.

```python

from eaglesong.demo.common import *
from eaglesong.drivers.telegram import TgCommand, TelegramSimplifier

def main():
    update = yield None
    username = update.message.chat.username
    chat_id = update.message.chat.id
    yield TgCommand.mock().send_message(
        chat_id = chat_id,
        text = f'Hello, {username}. Say anything and I will repeat. Or /start to reset.'
    )
    while True:
        update = yield Listen()
        message_text = update.message.text
        yield TgCommand.mock().send_message(chat_id=chat_id, text=message_text)

bot = Bot("telegram", TelegramSimplifier(main), add_telegram_filter=False)

if __name__ == '__main__':
    run(bot)
```

## Timers

The bots we saw so far were triggered by the user input. Sometimes the bots should be triggered by some other
means, and in this case the timer is used to poll the bot and produce the output if necessary.

This timer input is fed into the chatflow in the same fashion as the normal input.

```python
from eaglesong.demo.common import *

def main():
    timer_state = False
    timer_value = 0
    yield 'This bot will send you an integer every second. Enter /toggle to pause/resume'
    while True:
        input = yield Listen()
        if isinstance(input, TimerTick) and timer_state:
            yield timer_value
            timer_value += 1
        elif input=='/toggle':
            timer_state = not timer_state
            yield 'Timer set to '+str(timer_state)

bot = Bot("timer1", main, timer = True)

if __name__ == '__main__':
    run(bot)
```

### Advanced timer's handling

Such handling of the timer's signals brings the problem for the multi-step skills that expect
a certain input (such as menu). Obviously, they are going to be ruined by TimerTicks coming unexpectedly.

To avoid this, Timer signals have to be filtered out of normal flow. Here is the full code of how to do this.
At some point there will be some abstractions to make this in the easier way,
but at this point, let's see how it works under the hood. If you want to somehow manipulate with
input or outputs of skill A inside the skill B, you must isolate A inside the Automaton.
Automaton is an entity that translates these chatflows with all the `yield` into a normal function that
consumes one input and produces one output.

```python

from eaglesong.demo.common import *
from eaglesong.demo.example_08_menu_2 import create_menu

def main():
    context = yield ContextRequest()
    timer_state = False
    timer_value = 0
    menu_aut = None #type: Optional[Automaton]
    yield 'This bot will send you an integer every second. Enter /toggle to pause/resume, or /menu to open menu.'
    input = yield Listen()
    while True:
        if isinstance(input, TimerTick):
            if timer_state:
                yield timer_value
                timer_value+=1
            input = yield Listen()
            continue
        if input == '/toggle':
            timer_state = not timer_state
            yield 'Timer set to '+str(timer_state)
            input = yield Listen()
            continue

        if input == '/menu':
            menu_aut = Automaton(create_menu(), context)

        if menu_aut is not None:
            result = menu_aut.process(input)
            if isinstance(result, AutomatonExit):
                menu_aut = None
                input = yield Listen()
            else:
                input = yield result
            continue

        yield f'Unexpected input: {input}'
        input = yield Listen()

bot = Bot("timer2", main, timer=True)

if __name__ == '__main__':
    run(bot)
```


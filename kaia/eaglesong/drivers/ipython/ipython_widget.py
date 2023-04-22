import ipywidgets as widgets
from ...core import *
import time
import threading
from .ipython_interpreter import IPythonInterpreter

class IPythonChatWidget:
    def __init__(self,
                 interpreter: IPythonInterpreter,
                 timer=False,
                 warm_up_commands=('/start',),
                 bot_name=None
                 ):
        self.bot_name = bot_name if bot_name is not None else 'Kaia'
        self.timer = timer

        self.interpreter = interpreter
        self.input_field = widgets.Text()
        self.send_message = widgets.Button(description='Send')
        self.send_message.on_click(self.text_entered)
        self.timer_label = widgets.Label()
        self.timer_label.value = ' '
        self.stop_label = widgets.Label()
        self.is_typing_label = widgets.Label()
        self.chat = widgets.VBox()
        self.timer_state = 0

        for command in warm_up_commands:
            self.push(command)

    def on_timer(self):
        while (True):
            time.sleep(1)
            self.push(TimerTick())

    def text_entered(self, _):
        message = self.input_field.value
        self.input_field.value = ''
        self.push(message)

    def push(self, message):
        with threading.Lock():
            if isinstance(message, TimerTick):
                self.timer_label.value = '/-\|'[self.timer_state % 4]
                self.timer_state += 1
            if self.interpreter.has_exited():
                return
            self.interpreter.process(message)
            panels = self.create_message_panel()
            self.chat.children = panels
            self.stop_label.value = '🛑' if self.interpreter.has_exited() else ''
            self.is_typing_label.value = self.bot_name + ' is typing' if self.interpreter.model.is_typing else ''

    def push_button(self, button):
        self.push(SelectedOption(button.description))

    def convert_content(self, content):
        if isinstance(content, str) or isinstance(content, int) or isinstance(content, float):
            return widgets.Label(str(content))
        elif isinstance(content, Options):
            buttons = []
            for button_text in content.options:
                button = widgets.Button(description=button_text)
                button.on_click(self.push_button)
                buttons.append(button)
            return widgets.VBox([self.convert_content(content.content), widgets.HBox(buttons)])
        elif isinstance(content, SelectedOption) or isinstance(content, TimerTick):
            return None
        else:
            raise ValueError(f"Content of type {content} is not supported")

    def create_message_panel(self):
        panels = []
        layout = widgets.Layout(width='700px', border='1px solid black', margin='10px', background_color='red')
        placeholder = widgets.Layout(width='50px')
        for row in reversed(self.interpreter.model.messages):
            content = self.convert_content(row.content)
            if content is None:
                continue
            title = f'#{row.id} {self.bot_name if row.from_bot else "You"}:'
            label = widgets.Label(title)
            box = widgets.VBox([label, content], layout=layout)
            if row.from_bot:
                panels.append(widgets.HBox([box]))
            else:
                panels.append(widgets.HBox([widgets.Label(layout=placeholder), box]))
        return panels

    def run(self):
        if self.timer:
            thread = threading.Thread(target=self.on_timer)
            thread.start()
        return widgets.VBox([
            widgets.HBox([
                self.input_field,
                self.send_message,
                self.stop_label
            ]),
            widgets.HBox([
                self.timer_label,
                self.is_typing_label,
            ]),
            self.chat
        ])
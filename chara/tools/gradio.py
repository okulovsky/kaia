from typing import *
from gradio.events import Dependency

def dependency_feed(dep: Dependency, function: Callable[[Dependency], Dependency]):
    return function(dep)

Dependency.feed = dependency_feed

def empty_handler():
    pass
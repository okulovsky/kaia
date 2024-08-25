from typing import *
from dataclasses import dataclass
from pathlib import Path


class Command:
    @dataclass
    class Options:
        workdir: str | Path | None = None
        return_output: bool = False

    @dataclass
    class Comment:
        comment: str

    Acceptable = Iterable[Union[str,Path, Comment]]

    @staticmethod
    def convert(command: 'Command.Acceptable') -> Union['Command',None]:
        result = []
        comments = {}
        for c in command:
            if isinstance(c, str) or isinstance(c, Path):
                result.append(str(c))
            elif isinstance(c, Command.Comment):
                comments[c.comment] = len(result)
            else:
                return None
        return Command(tuple(result), None, comments if len(comments) > 0 else None)


    def __init__(self,
                 command: 'Command.Acceptable',
                 options: Optional['Command.Options'] = None,
                 comments: None|dict[str,int] = None
                 ):
        if isinstance(command, tuple) and all(isinstance(c, str) for c in command):
            self.command = command
            self.options = options
            self.comments = comments
        else:
            cmd = Command.convert(command)
            self.command = cmd.command
            self.options = options
            if cmd.comments is not None and comments is not None:
                raise ValueError("Comments should come either from constructor for 'pure' command, or from command itself if it is to be converted. TLDR: remove `comments` argument")
            self.comments = cmd.comments



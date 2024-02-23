from typing import *
import subprocess
from dataclasses import dataclass

@dataclass
class SubprocessResult:
    return_code: int
    command: Union[str, Iterable[str]]
    input: Optional[str]
    output: bytes
    errors: Optional[bytes]

    @property
    def str_output(self) -> str:
        if isinstance(self.output, str):
            return self.output
        return self.output.decode('utf-8')

    @property
    def str_errors(self) -> str:
        if isinstance(self.errors, str):
            return self.errors
        return self.errors.decode('utf-8')

    @property
    def str_command(self) -> str:
        if isinstance(self.command, str):
            return self.command
        else:
            return ' '.join(str(s) for s in self.command)

    def if_fails(self, message) -> 'SubprocessResult':
        if self.return_code != 0:
            try:
                o = self.str_output
            except:
                o = self.output
            try:
                e = self.str_errors
            except:
                e = self.errors
            m = message
            m+="\n=== Command: ===\n"+self.str_command
            if self.input is not None:
                m += "\n=== Input: ===\n" + self.input
            if o is not None and len(o)!=0:
                m += '\n=== Output: ===\n'+o
            if e is not None and len(e)!=0:
                m += '\n=== Errors: ===\n'+e
            raise ValueError(m)


        return self


def subprocess_call(args, **kwargs) -> SubprocessResult:
    try:
        output = subprocess.check_output(args, **kwargs, stderr=subprocess.STDOUT)
        return SubprocessResult(0, args, None, output, b'')
    except subprocess.CalledProcessError as exc:
        return SubprocessResult(exc.returncode, args, None, exc.output, b'')


def subprocess_push_input(args, input: str, **kwargs) -> SubprocessResult:
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, input=input.encode('ascii'), **kwargs)
    return SubprocessResult(process.returncode, args, input, process.stdout, process.stderr)


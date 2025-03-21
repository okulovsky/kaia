import traceback

from .command import  Command
import subprocess
from dataclasses import dataclass
import threading


@dataclass
class ExecutionScenario:
    command: tuple[str,...]
    options: Command.Options
    command_as_str: str
    call_kwargs: dict


    _monitored_output = None

    def _to_str(self, output):
        if isinstance(output, str):
            return output
        try:
            return output.decode('utf-8')
        except:
            return output

    def _execute_with_no_output_control(self):
        try:
            result = subprocess.call(self.command, **self.call_kwargs)
        except Exception as ex:
            raise ValueError(f"Error launching subprocess, arguments:\n{self.command_as_str}") from ex
        if result != 0:
            if self.options.ignore_exit_code:
                pass
            else:
                raise ValueError(f'Error running subprocess, arguments:\n{self.command_as_str}')
        return None

    def _execute_with_return_output(self):
        try:
            output = subprocess.check_output(self.command, **self.call_kwargs, stderr=subprocess.STDOUT)
            return self._to_str(output)
        except subprocess.CalledProcessError as exc:
            o_str = self._to_str(exc.output)
            if self.options.ignore_exit_code:
                return o_str
            else:
                raise ValueError(f'Error running subprocess, arguments:\n{self.command_as_str}\noutput\n{o_str}')


    def _monitor(self, stream):
        """Reads lines from the stream and calls the callback with each line."""
        try:
            for line in iter(stream.readline, ""):
                if line=='':
                    break
                no_newline = line
                if no_newline.endswith('\n'):
                    no_newline = no_newline[:-1]
                self.options.monitor_output(no_newline)
                self._monitored_output.append(no_newline)

            stream.close()
        except:
            ex = traceback.format_exc()
            self.options.monitor_output("Error when reading stream. The process continues to run, but the monitoring is broken")
            self.options.monitor_output(ex)


    def _execute_with_monitoring(self):
        self._monitored_output = []
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **self.call_kwargs,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )

            stdout_thread = threading.Thread(target=self._monitor, args=(process.stdout,), daemon=True)
            stderr_thread = threading.Thread(target=self._monitor, args=(process.stderr,), daemon=True)

            stdout_thread.start()
            stderr_thread.start()

            process.wait()

            stdout_thread.join()
            stderr_thread.join()

        except Exception as ex:
            raise ValueError(f"Error launching subprocess, arguments:\n{self.command_as_str}") from ex

        if process.returncode != 0:
            if not self.options.ignore_exit_code:
                raise ValueError(f'Error running subprocess, arguments:\n{self.command_as_str}\noutput\n'+"\n".join(self._monitored_output[-50:]))

        return "\n".join(self._monitored_output)



    def  execute(self):
        if self.options.monitor_output is not None:
            return self._execute_with_monitoring()
        elif self.options.return_output:
            return self._execute_with_return_output()
        else:
            return self._execute_with_no_output_control()




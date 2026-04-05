import sys
from unittest import TestCase
from foundation_kaia.brainbox_utils.training import subprocess_streaming_call, SubprocessError


class SubprocessStreamingCallTestCase(TestCase):
    def _collect(self, cmd) -> list[str]:
        return list(subprocess_streaming_call(cmd))

    def test_captures_stdout(self):
        lines = self._collect([sys.executable, '-c', 'print("hello"); print("world")'])
        self.assertEqual(['hello', 'world'], lines)

    def test_captures_stderr(self):
        lines = self._collect([sys.executable, '-c', 'import sys; sys.stderr.write("err line\\n")'])
        self.assertEqual(['err line'], lines)

    def test_captures_mixed_stdout_and_stderr(self):
        script = 'import sys; print("out1"); sys.stderr.write("err1\\n"); print("out2")'
        lines = self._collect([sys.executable, '-c', script])
        self.assertIn('out1', lines)
        self.assertIn('err1', lines)
        self.assertIn('out2', lines)

    def test_captures_output_before_crash(self):
        script = 'print("before crash"); raise RuntimeError("boom")'
        lines = []
        with self.assertRaises(SubprocessError):
            for line in subprocess_streaming_call([sys.executable, '-c', script]):
                lines.append(line)
        self.assertIn('before crash', lines)

    def test_captures_traceback_on_crash(self):
        script = 'print("before"); raise RuntimeError("boom")'
        lines = []
        with self.assertRaises(SubprocessError):
            for line in subprocess_streaming_call([sys.executable, '-c', script]):
                lines.append(line)
        all_output = '\n'.join(lines)
        self.assertIn('RuntimeError', all_output)
        self.assertIn('boom', all_output)

    def test_raises_subprocess_error_on_nonzero_exit(self):
        with self.assertRaises(SubprocessError) as ctx:
            self._collect([sys.executable, '-c', 'import sys; sys.exit(42)'])
        self.assertEqual(42, ctx.exception.returncode)

    def test_no_error_on_zero_exit(self):
        lines = self._collect([sys.executable, '-c', 'pass'])
        self.assertEqual([], lines)

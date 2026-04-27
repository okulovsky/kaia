import threading
import time
import unittest
from pathlib import Path
import tempfile

from brainbox.framework.common.streaming import StreamingStorage


class TestStreamingStorageCheckFilename(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = StreamingStorage(Path(self.tmpdir))

    def test_filename_with_slash_raises(self):
        with self.assertRaises(ValueError):
            self.storage._check_filename('folder/file.txt')

    def test_filename_without_slash_ok(self):
        self.storage._check_filename('file.txt')  # should not raise

    def test_empty_filename_ok(self):
        self.storage._check_filename('')  # no slash, should not raise

    def test_slash_only_raises(self):
        with self.assertRaises(ValueError):
            self.storage._check_filename('/')

    def test_leading_slash_raises(self):
        with self.assertRaises(ValueError):
            self.storage._check_filename('/etc/passwd')


class TestStreamingStorageCommittedFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = StreamingStorage(Path(self.tmpdir))

    def _write_and_commit(self, filename, chunks):
        self.storage.begin_writing(filename)
        for chunk in chunks:
            self.storage.append(filename, chunk)
        self.storage.commit(filename)

    def test_read_committed_single_chunk(self):
        self._write_and_commit('test.bin', [b'hello'])
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'hello', result)

    def test_read_committed_multiple_chunks(self):
        self._write_and_commit('test.bin', [b'abc', b'def', b'ghi'])
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'abcdefghi', result)

    def test_read_committed_empty_file(self):
        self._write_and_commit('empty.bin', [])
        result = b''.join(self.storage.read('empty.bin'))
        self.assertEqual(b'', result)

    def test_double_commit_raises(self):
        self._write_and_commit('test.bin', [b'data'])
        with self.assertRaises(ValueError):
            self.storage.commit('test.bin')

    def test_begin_writing_overwrites_existing(self):
        self._write_and_commit('test.bin', [b'old data'])
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'new data')
        self.storage.commit('test.bin')
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'new data', result)

    def test_delete_committed_file(self):
        self._write_and_commit('test.bin', [b'data'])
        self.storage.delete('test.bin')
        with self.assertRaises(FileNotFoundError):
            list(self.storage.read('test.bin'))

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(ValueError):
            self.storage.delete('nonexistent.bin')

    def test_read_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            list(self.storage.read('nonexistent.bin'))

    def test_no_tempfile_after_commit(self):
        self._write_and_commit('test.bin', [b'data'])
        tmp = Path(self.tmpdir) / 'test.bin.streaming_tempfile'
        self.assertFalse(tmp.exists())

    def test_tempfile_exists_during_writing(self):
        self.storage.begin_writing('test.bin')
        tmp = Path(self.tmpdir) / 'test.bin.streaming_tempfile'
        self.assertTrue(tmp.exists())
        self.storage.commit('test.bin')


class TestStreamingStorageLiveStream(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = StreamingStorage(Path(self.tmpdir))

    def test_live_stream_basic(self):
        chunks_written = [b'chunk1', b'chunk2', b'chunk3']
        received = []

        def writer():
            self.storage.begin_writing('live.bin')
            for chunk in chunks_written:
                time.sleep(0.02)
                self.storage.append('live.bin', chunk)
            self.storage.commit('live.bin')

        t = threading.Thread(target=writer)
        t.start()
        time.sleep(0.01)  # Let writer start

        for chunk in self.storage.read('live.bin'):
            received.append(chunk)

        t.join()
        self.assertEqual(b''.join(chunks_written), b''.join(received))

    def test_live_stream_large_data(self):
        data = b'x' * 200_000
        received = []

        def writer():
            self.storage.begin_writing('big.bin')
            chunk_size = 50_000
            for i in range(0, len(data), chunk_size):
                self.storage.append('big.bin', data[i:i + chunk_size])
            self.storage.commit('big.bin')

        t = threading.Thread(target=writer)
        t.start()
        time.sleep(0.01)  # Let writer start and create the file

        for chunk in self.storage.read('big.bin'):
            received.append(chunk)
        t.join()
        self.assertEqual(data, b''.join(received))


class TestStreamingStorageChunkIndex(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = StreamingStorage(Path(self.tmpdir))

    def _write_indexed_and_commit(self, filename, indexed_chunks):
        self.storage.begin_writing(filename)
        for index, chunk in indexed_chunks:
            self.storage.append(filename, chunk, chunk_index=index)
        self.storage.commit(filename)

    def test_in_order_indexed_chunks(self):
        self._write_indexed_and_commit('test.bin', [(0, b'a'), (1, b'b'), (2, b'c')])
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'abc', result)

    def test_two_chunks_out_of_order(self):
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'b', chunk_index=1)
        self.storage.append('test.bin', b'a', chunk_index=0)
        self.storage.commit('test.bin')
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'ab', result)

    def test_three_chunks_reversed(self):
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'c', chunk_index=2)
        self.storage.append('test.bin', b'b', chunk_index=1)
        self.storage.append('test.bin', b'a', chunk_index=0)
        self.storage.commit('test.bin')
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'abc', result)

    def test_multiple_buffered_chunks_flushed_at_once(self):
        # chunks 1, 2, 3 arrive before 0; sending 0 should flush all of them
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'b', chunk_index=1)
        self.storage.append('test.bin', b'c', chunk_index=2)
        self.storage.append('test.bin', b'd', chunk_index=3)
        self.storage.append('test.bin', b'a', chunk_index=0)
        self.storage.commit('test.bin')
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'abcd', result)

    def test_no_index_unaffected(self):
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'x')
        self.storage.append('test.bin', b'y')
        self.storage.commit('test.bin')
        result = b''.join(self.storage.read('test.bin'))
        self.assertEqual(b'xy', result)

    def test_out_of_order_live_stream(self):
        received = []

        def writer():
            self.storage.begin_writing('live.bin')
            time.sleep(0.02)
            self.storage.append('live.bin', b'second', chunk_index=1)
            time.sleep(0.02)
            self.storage.append('live.bin', b'first', chunk_index=0)
            self.storage.commit('live.bin')

        t = threading.Thread(target=writer)
        t.start()
        time.sleep(0.01)

        for chunk in self.storage.read('live.bin'):
            received.append(chunk)

        t.join()
        self.assertEqual(b'firstsecond', b''.join(received))

    def test_buffer_cleared_after_commit(self):
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'a', chunk_index=0)
        self.storage.commit('test.bin')
        self.assertNotIn('test.bin', self.storage.buffer)
        self.assertNotIn('test.bin', self.storage.current_chunks)

    def test_buffer_cleared_after_delete(self):
        self.storage.begin_writing('test.bin')
        self.storage.append('test.bin', b'a', chunk_index=0)
        self.storage.delete('test.bin')
        self.assertNotIn('test.bin', self.storage.buffer)
        self.assertNotIn('test.bin', self.storage.current_chunks)


if __name__ == '__main__':
    unittest.main()

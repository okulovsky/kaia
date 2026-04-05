from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def downloads(test_case: TestCase, api: BrainBox.Api):
    """
    ### Download files produced by deciders

    Many BrainBox deciders return files with generated audio or images.
    In order not to overload the BrainBox database with all these
    gigabytes, the files are stored in the cache folder,
    and only the file names are returned.
    """

    filename = api.execute(HelloBrainBox.new_task().voiceover('Hello, file!', HelloBrainBox.Models.google))
    test_case.assertIsInstance(filename, str)

    """
    You may open this file with `api.cache.read_file` method, which returns a `File`
    instance, reading the content of the file on the fly.
    """

    from brainbox import File
    import json

    file = api.cache.read_file(filename)
    test_case.assertIsInstance(file, File)
    content = json.loads(file.content)
    test_case.assertEqual('Hello, file!', content['text'])
    test_case.assertIn('google', content['model'])

    """
    If you don't want to open the file, only download it to disk:
    """
    from pathlib import Path
    import tempfile

    path = api.cache.download(filename, Path(tempfile.gettempdir()))
    test_case.assertIsInstance(path, Path)
    with open(path, 'rb') as stream:
        content = json.loads(stream.read())
    test_case.assertEqual('Hello, file!', content['text'])

    """
    which simply downloads the file to the given folder and returns the full path to the file.
    You may specify any target folder; the file is placed there under its original name.
    
    There is also an option to `.read` only the content of the file, or `.open` it to get the Iterable of bytes. 
    """



from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def downloads(test_case: TestCase, api: BrainBox.Api):
    """
    ### Download files, produced by deciders

    Many BrainBox deciders return files with generated images or sounds.
    In order not to overload the BrainBox database with all these
    gigabytes, the files are stored in the cache folder,
    and only files' names are returned.
    """

    filename = api.execute(BrainBox.Task.call(HelloBrainBox).file("Hello, file!"))
    test_case.assertIsInstance(filename, str)

    """
    You may open this file with `api.open_file` method, which returns `File` 
    instance, reading the content of the file on the fly. 
    """

    from brainbox import File
    import json

    file = api.open_file(filename)
    test_case.assertIsInstance(file, File)
    test_case.assertDictEqual(
        {
            'argument': 'Hello, file!',
            'model': 'no_parameter',
            'setting': 'default_setting'
        },
        json.loads(file.content)
    )

    """
    If you don't want to open the file, only download it on the disk:
    """
    from pathlib import Path

    path = api.download(filename)
    test_case.assertIsInstance(path, Path)
    with open(path, 'r') as stream:
        test_case.assertDictEqual(
            {
                'argument': 'Hello, file!',
                'model': 'no_parameter',
                'setting': 'default_setting'
            },
            json.load(stream)
        )

    """
    which simply downloads the file on the disk to the given location
    (by default, in the API's cache folder), and returns the full path to file.
    You may specify the location and the flag to redownload the file even
    if it was already downloaded.
    """

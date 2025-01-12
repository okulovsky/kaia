from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def uploads(test_case: TestCase, api: BrainBox.Api):
    """
    ### Upload files, required by deciders
    
    Some deciders, especially speech-to-text or image analysis, 
    use files as inputs. You may feed them directly in the call:
    """
    from brainbox import File

    file = File('hello.txt', "Hello, world!")
    test_case.assertEqual(file.name, 'hello.txt')
    test_case.assertEqual(file.content, b'Hello, world!')

    length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file))
    test_case.assertEqual(length, 13)

    """
    However, that has the potential to overload the database as well, 
    and should be avoided.
    
    If you run BrainBox server at the machine you're running `api`, 
    you may pass the path of the file:

    ```python
    import tempfile
    from pathlib import Path

    path = file.write(tempfile.gettempdir())
    test_case.assertIsInstance(path, Path)

    length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(path))
    test_case.assertEqual(length, 13)
    ```
    
    This solution is dirty as it won't work with a remote BrainBox, 
    and would force you to rewrite your codebase in case of such change.
    
    To avoid this, you may choose to upload the file to the BrainBox
    cache folder instead:
    """

    api.upload(file.name, file)
    length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file.name))
    test_case.assertEqual(length, 13)

    """
    Sometimes, files are required to have specific names, or some
    recoding. In these cases, deciders usually have static methods
    that incapsulate these procedures in Prerequisites:
    """
    upload_prerequisite = HelloBrainBox.file_upload(file)
    upload_prerequisite.execute(api)
    length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file.name))
    test_case.assertEqual(length, 13)

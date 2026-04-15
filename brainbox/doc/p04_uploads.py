from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def uploads(test_case: TestCase, api: BrainBox.Api):
    """
    ### Upload files required by deciders

    Some deciders, especially speech-to-text or audio analysis,
    use files as inputs. You may feed bytes directly in the call:
    """
    data = b'12112'
    result = api.execute(HelloBrainBox.new_task().voice_embedding(data))
    test_case.assertEqual(3, result[1])
    test_case.assertEqual(2, result[2])

    """
    `HelloBrainBox::voice_embedding` counts the occurrences of bytes from `0` to `9` value
    and returns a list of 10 counts — one per possible byte value.

    However, passing large binary data inline has the potential to overload the
    database, and should be avoided for large files.

    To avoid this, you may choose to upload the file to the BrainBox
    cache folder instead:
    """

    from brainbox import File

    file = File('audio.bin', b'12112')
    api.cache.upload(file.name, file)
    result = api.execute(HelloBrainBox.new_task().voice_embedding(file.name))
    test_case.assertEqual(3, result[ord(b'1')])
    test_case.assertEqual(2, result[ord(b'2')])

    """
    By uploading the file to the cache folder first, you decouple the data
    transfer from the task execution. The decider receives only the filename
    and reads the file from the shared cache.
    
    This solution scales to remote BrainBox instances as well,
    since the upload is handled separately from the task.
    """

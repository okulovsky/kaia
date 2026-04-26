from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

voice_embedding_1 = ControlValue.mddoc_define_control_value([0.0, 3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

if __name__ == '__main__':
    """
    ### Upload files required by deciders

    Some deciders, especially speech-to-text or audio analysis,
    use files as inputs. You may feed bytes directly in the call:
    """
    data = b'12112'
    result = api.execute(HelloBrainBox.new_task().voice_embedding(data))

    """
    This decider counts the occurrences of bytes from `0` to `9` value
    and returns a list of 10 counts — one per possible byte value, so the result is:
    """

    voice_embedding_1.mddoc_validate_control_value(result)

    """
    However, passing large binary data inline has the potential to overload the
    database, and should be avoided for large files.

    To avoid this, you may choose to upload the file to the BrainBox
    cache folder instead:
    """

    from brainbox import File

    api.cache.upload('test', b'12112')
    result = api.execute(HelloBrainBox.new_task().voice_embedding('test'))

    """
    The result will remain the same:
    """

    voice_embedding_1.mddoc_validate_control_value(result)

    """
    By uploading the file to the cache folder first, you decouple the data
    transfer from the task execution. The decider receives only the filename
    and reads the file from the shared cache.
    
    This solution scales to remote BrainBox instances as well,
    since the upload is handled separately from the task.
    """

import ctypes
import glob
import os
from ctypes import Structure, POINTER, byref, c_bool, c_char_p, c_float, c_int32, c_size_t, c_void_p
import numpy as np


class _BackendConfig(Structure):
    _fields_ = [('size', c_size_t), ('gpu', c_int32)]


class _ModelConfig(Structure):
    _fields_ = [('size', c_size_t), ('path', c_char_p), ('name', c_char_p)]


class _StreamingConfig(Structure):
    _fields_ = [
        ('size', c_size_t),
        ('chunk_size', c_float),
        ('ctc_left_padding', c_float),
        ('ctc_right_padding', c_float),
        ('rnnt_right_context', c_int32),
    ]


class _RecognizerConfig(Structure):
    _fields_ = [
        ('size', c_size_t),
        ('backend', POINTER(_BackendConfig)),
        ('model', POINTER(_ModelConfig)),
        ('streaming', POINTER(_StreamingConfig)),
        ('decoder', c_void_p),
        ('vad', c_void_p),
        ('endpointing', c_void_p),
        ('postproc', c_void_p),
        ('diar', c_void_p),
        ('batching', c_void_p),
    ]


class _RecognitionOptions(Structure):
    _fields_ = [
        ('size', c_size_t),
        ('request_id', c_char_p),
        ('language_code', c_char_p),
        ('interim_results', c_bool),
        ('enable_word_time_offsets', c_bool),
        ('enable_automatic_punctuation', c_bool),
        ('verbatim_transcripts', c_bool),
        ('profanity_filter', c_bool),
        ('stop_history_eou_ms', c_int32),
        ('speech_contexts', c_void_p),
        ('speech_context_count', c_size_t),
        ('max_alternatives', c_int32),
        ('enable_speaker_diarization', c_bool),
        ('max_speaker_count', c_int32),
    ]


def _find_library() -> str:
    explicit = os.environ.get('NEMO_SPEECH_ASR_LIB')
    if explicit:
        return explicit
    for root in ('/opt/nemo-speech', '/usr/local'):
        found = glob.glob(f'{root}/**/libnemo_speech_asr_c.so*', recursive=True)
        if found:
            return sorted(found)[0]
    raise FileNotFoundError("libnemo_speech_asr_c.so was not found; set NEMO_SPEECH_ASR_LIB")


def _load_library():
    lib = ctypes.CDLL(_find_library())
    p_rec = c_void_p
    p_stream = c_void_p
    p_result = c_void_p
    lib.nemo_speech_asr_last_error.restype = c_char_p
    lib.nemo_speech_asr_recognition_options_default.restype = _RecognitionOptions
    lib.nemo_speech_asr_create.argtypes = [POINTER(_RecognizerConfig), POINTER(p_rec)]
    lib.nemo_speech_asr_destroy.argtypes = [p_rec]
    lib.nemo_speech_asr_recognize_f32.argtypes = [
        p_rec, POINTER(_RecognitionOptions), POINTER(c_float), c_size_t, c_int32, POINTER(p_result)]
    lib.nemo_speech_asr_streaming_recognize.argtypes = [
        p_rec, POINTER(_RecognitionOptions), POINTER(p_stream)]
    lib.nemo_speech_asr_stream_push_f32.argtypes = [p_stream, POINTER(c_float), c_size_t, c_int32]
    lib.nemo_speech_asr_stream_finish.argtypes = [p_stream]
    lib.nemo_speech_asr_stream_next.argtypes = [p_stream, POINTER(p_result)]
    lib.nemo_speech_asr_stream_close.argtypes = [p_stream]
    lib.nemo_speech_asr_result_is_final.argtypes = [p_result]
    lib.nemo_speech_asr_result_is_final.restype = c_bool
    lib.nemo_speech_asr_result_transcript.argtypes = [p_result, c_size_t]
    lib.nemo_speech_asr_result_transcript.restype = c_char_p
    lib.nemo_speech_asr_result_word_count.argtypes = [p_result, c_size_t]
    lib.nemo_speech_asr_result_word_count.restype = c_size_t
    lib.nemo_speech_asr_result_word_text.argtypes = [p_result, c_size_t, c_size_t]
    lib.nemo_speech_asr_result_word_text.restype = c_char_p
    lib.nemo_speech_asr_result_word_start_time.argtypes = [p_result, c_size_t, c_size_t]
    lib.nemo_speech_asr_result_word_start_time.restype = c_int32
    lib.nemo_speech_asr_result_word_end_time.argtypes = [p_result, c_size_t, c_size_t]
    lib.nemo_speech_asr_result_word_end_time.restype = c_int32
    lib.nemo_speech_asr_result_word_confidence.argtypes = [p_result, c_size_t, c_size_t]
    lib.nemo_speech_asr_result_word_confidence.restype = c_float
    lib.nemo_speech_asr_result_language_count.argtypes = [p_result, c_size_t]
    lib.nemo_speech_asr_result_language_count.restype = c_size_t
    lib.nemo_speech_asr_result_language_code.argtypes = [p_result, c_size_t, c_size_t]
    lib.nemo_speech_asr_result_language_code.restype = c_char_p
    lib.nemo_speech_asr_result_destroy.argtypes = [p_result]
    return lib


_lib = None


def _get_lib():
    global _lib
    if _lib is None:
        _lib = _load_library()
    return _lib


def _check(status: int):
    if status != 0:
        message = _get_lib().nemo_speech_asr_last_error()
        raise RuntimeError(f"NeMo-Speech.cpp error {status}: {message.decode() if message else ''}")


def _read_result(result) -> dict:
    lib = _get_lib()
    words = []
    for i in range(lib.nemo_speech_asr_result_word_count(result, 0)):
        words.append(dict(
            word=lib.nemo_speech_asr_result_word_text(result, 0, i).decode(),
            start_time=lib.nemo_speech_asr_result_word_start_time(result, 0, i),
            end_time=lib.nemo_speech_asr_result_word_end_time(result, 0, i),
            confidence=lib.nemo_speech_asr_result_word_confidence(result, 0, i),
        ))
    languages = [
        lib.nemo_speech_asr_result_language_code(result, 0, i).decode()
        for i in range(lib.nemo_speech_asr_result_language_count(result, 0))
    ]
    return dict(
        text=lib.nemo_speech_asr_result_transcript(result, 0).decode(),
        is_final=bool(lib.nemo_speech_asr_result_is_final(result)),
        language=languages[0] if languages else None,
        languages=languages,
        words=words,
    )


def _options(language: str, interim_results: bool) -> _RecognitionOptions:
    options = _get_lib().nemo_speech_asr_recognition_options_default()
    options.language_code = (language or 'auto').encode()
    options.interim_results = interim_results
    options.enable_word_time_offsets = True
    return options


def _as_float_pointer(samples: np.ndarray):
    samples = np.ascontiguousarray(samples, dtype=np.float32)
    return samples, samples.ctypes.data_as(POINTER(c_float))


class NemoStream:
    def __init__(self, recognizer: 'NemoRecognizer', language: str):
        self._options = _options(language, True)
        self._handle = c_void_p()
        _check(_get_lib().nemo_speech_asr_streaming_recognize(
            recognizer._handle, byref(self._options), byref(self._handle)))

    def push(self, samples: np.ndarray, sample_rate: int):
        keep, pointer = _as_float_pointer(samples)
        _check(_get_lib().nemo_speech_asr_stream_push_f32(self._handle, pointer, len(keep), sample_rate))

    def finish(self):
        _check(_get_lib().nemo_speech_asr_stream_finish(self._handle))

    def poll(self) -> list[dict]:
        lib = _get_lib()
        results = []
        while True:
            result = c_void_p()
            _check(lib.nemo_speech_asr_stream_next(self._handle, byref(result)))
            if not result:
                return results
            try:
                results.append(_read_result(result))
            finally:
                lib.nemo_speech_asr_result_destroy(result)

    def close(self):
        if self._handle:
            _get_lib().nemo_speech_asr_stream_close(self._handle)
            self._handle = c_void_p()


class NemoRecognizer:
    def __init__(self, model_path: str, rnnt_right_context: int = 1):
        lib = _get_lib()
        backend = _BackendConfig(ctypes.sizeof(_BackendConfig), -1)
        model = _ModelConfig(ctypes.sizeof(_ModelConfig), model_path.encode(), None)
        streaming = _StreamingConfig(ctypes.sizeof(_StreamingConfig), 0.16, 1.92, 1.92, rnnt_right_context)
        config = _RecognizerConfig(ctypes.sizeof(_RecognizerConfig))
        config.backend = ctypes.pointer(backend)
        config.model = ctypes.pointer(model)
        config.streaming = ctypes.pointer(streaming)
        self._handle = c_void_p()
        _check(lib.nemo_speech_asr_create(byref(config), byref(self._handle)))

    def recognize(self, samples: np.ndarray, sample_rate: int, language: str = 'auto') -> dict:
        lib = _get_lib()
        options = _options(language, False)
        keep, pointer = _as_float_pointer(samples)
        result = c_void_p()
        _check(lib.nemo_speech_asr_recognize_f32(
            self._handle, byref(options), pointer, len(keep), sample_rate, byref(result)))
        try:
            return _read_result(result)
        finally:
            lib.nemo_speech_asr_result_destroy(result)

    def open_stream(self, language: str = 'auto') -> NemoStream:
        return NemoStream(self, language)

    def close(self):
        if self._handle:
            _get_lib().nemo_speech_asr_destroy(self._handle)
            self._handle = c_void_p()

    def __del__(self):
        self.close()

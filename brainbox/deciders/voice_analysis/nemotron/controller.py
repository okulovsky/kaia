import difflib
import json
import re
from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
)
from .settings import NemotronSettings
from pathlib import Path
from .app.model import NemotronInstaller

NEMO_SPEECH_COMMIT = '4c101bc7113f49101a3e11d2c994c519f41939f6'
INSTALL_PREFIX = '/opt/nemo-speech'

BUILD_NEMO_SPEECH = (
    'USER root',
    f'RUN git clone https://github.com/NVIDIA/NeMo-Speech.cpp /tmp/nemo-src && '
    f'cd /tmp/nemo-src && git checkout {NEMO_SPEECH_COMMIT} && '
    f'git submodule update --init --depth 1 ggml llama.cpp && '
    f'scripts/configure.sh cpu-asr && '
    f'cmake --build --preset cpu-asr && '
    f'cmake --install build/cpu-asr --prefix {INSTALL_PREFIX} && '
    f'find {INSTALL_PREFIX} -name "*.so*" -exec dirname {{}} \\; | sort -u > /etc/ld.so.conf.d/nemo-speech.conf && '
    f'ldconfig && '
    f'rm -rf /tmp/nemo-src',
    'USER app',
)

SAMPLES = (
    ('timer_en.wav', 'en-US', 'en', 'set the timer for five minutes'),
    ('timer_de.wav', 'de-DE', 'de', 'stelle den timer auf fünf minuten'),
)

CHUNK_SIZE = 7056


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()


def _assert_text(tc, expected: str, actual: str):
    ratio = difflib.SequenceMatcher(None, expected, _normalize(actual)).ratio()
    tc.assertGreaterEqual(ratio, 0.85, f"expected '{expected}', got '{actual}'")


def _parse_events(content: bytes) -> list[dict]:
    decoder = json.JSONDecoder()
    text = content.decode('utf-8')
    events = []
    pos = 0
    while pos < len(text):
        event, pos = decoder.raw_decode(text, pos)
        events.append(event)
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return events


class NemotronController(DockerMarshallingController[NemotronSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('git', 'build-essential', 'ninja-build', 'pkg-config', 'libsentencepiece-dev'),
            allow_arm64=True,
            custom_apt_installation=('RUN pip install --no-cache-dir "cmake>=3.26"',),
            finishing_installation_steps=BUILD_NEMO_SPEECH,
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            )
        )

    def get_service_run_configuration(self, port: int, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={port: 8080},
        )

    def get_installer(self) -> Installer | None:
        return NemotronInstaller(self.resource_folder())

    def get_default_settings(self):
        return NemotronSettings()

    def get_loading_time_in_seconds(self) -> int:
        return 30

    def create_api(self, base_url: str):
        from .api import NemotronApi
        return NemotronApi(base_url)

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Nemotron
        folder = Path(__file__).parent / 'files'

        for filename, locale, language, expected in SAMPLES:
            data = (folder / filename).read_bytes()
            file = File.read(folder / filename)

            def check_offline(result, api, tc, expected=expected):
                _assert_text(tc, expected, result['text'])
                tc.assertGreater(len(result['words']), 0)
            yield SelfTestCase(Nemotron.new_task().transcribe(file, locale), check_offline)

            def check_auto(result, api, tc, expected=expected, language=language):
                _assert_text(tc, expected, result['text'])
                if result['languages']:
                    tc.assertTrue(result['language'].lower().startswith(language), str(result))
            yield SelfTestCase(Nemotron.new_task().transcribe(file, 'auto'), check_auto)

            chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]

            def check_stream(result, api, tc, expected=expected):
                events = _parse_events(api.cache.read_file(result).content)
                tc.assertGreater(len(events), 1)
                tc.assertTrue(events[-1]['is_final'])
                tc.assertFalse(any(e['is_final'] for e in events[:-1]))
                _assert_text(tc, expected, events[-1]['text'])
            yield SelfTestCase(Nemotron.new_task().transcribe_stream(chunks, locale), check_stream)

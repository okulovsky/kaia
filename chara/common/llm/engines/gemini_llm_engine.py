import base64
import mimetypes
import os
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from brainbox import BrainBox
from brainbox.deciders import Ollama

from .llm_engine import ILLMEngine
from .ollama_task_view import OllamaTaskView


class GeminiLLMEngine(ILLMEngine):
    """Talks to Gemini through its OpenAI-compatible endpoint, so switching to
    another OpenAI-compatible provider later only means changing base_url/model."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self, api_key: str|None = None, debug: bool = False, max_parallel_calls: int = 8):
        from openai import OpenAI
        self.debug = debug
        self.client = OpenAI(api_key=api_key or os.environ['GEMINI_API_KEY'], base_url=self.BASE_URL)
        # The OpenAI client is synchronous, so `start` hands the call to a thread and
        # returns its Future; several requests started before the first join overlap.
        self._executor = ThreadPoolExecutor(max_workers=max_parallel_calls, thread_name_prefix='gemini')

    def _build_kwargs(self, options: Optional[Ollama.Options]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if options is None:
            return kwargs

        # Direct equivalents in the OpenAI chat-completions schema.
        if options.temperature is not None:
            kwargs['temperature'] = options.temperature
        if options.top_p is not None:
            kwargs['top_p'] = options.top_p
        if options.stop is not None:
            kwargs['stop'] = options.stop
        if options.seed is not None:
            kwargs['seed'] = options.seed
        if options.num_predict is not None:
            kwargs['max_tokens'] = options.num_predict
        if options.format is not None:
            if options.format == 'json':
                kwargs['response_format'] = {'type': 'json_object'}
            elif isinstance(options.format, dict):
                kwargs['response_format'] = {
                    'type': 'json_schema',
                    'json_schema': {'name': 'response', 'schema': options.format, 'strict': True},
                }

        # top_k isn't part of the OpenAI schema, but Gemini's own GenerationConfig
        # has it; the OpenAI-compat layer exposes it through this escape hatch.
        if options.top_k is not None:
            kwargs['extra_body'] = {'extra_body': {'google': {'top_k': options.top_k}}}

        # No equivalent in Gemini's hosted API, so these are intentionally dropped:
        # - min_p, mirostat/mirostat_tau/mirostat_eta: sampler not implemented by Gemini.
        # - repeat_penalty: exists in spirit as frequency_penalty, but the scales are
        #   incompatible (Ollama's is multiplicative around 1.0, OpenAI's is additive
        #   around 0), so a direct copy would silently misbehave.
        # - repeat_last_n: no windowed-penalty concept in Gemini's API.
        # - num_ctx, num_gpu, num_thread: hosted API, no local context/hardware control.

        return kwargs

    @staticmethod
    def _image_content(image: Path) -> dict:
        if not isinstance(image, Path):
            raise ValueError(f"Image must be a Path, but was {type(image)}")
        mime = mimetypes.guess_type(image.name)[0] or 'image/png'
        data = base64.b64encode(image.read_bytes()).decode('ascii')
        return {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{data}'}}

    def start(self, task: BrainBox.Task) -> Future:
        self.report_task(task)
        return self._executor.submit(self._call, OllamaTaskView.parse(task))

    def join(self, token: Future) -> str:
        result = token.result()
        self.report_answer(result)
        return result

    def _call(self, view: OllamaTaskView) -> str:
        messages = []
        if view.system_prompt is not None:
            messages.append({"role": "system", "content": view.system_prompt})
        if view.image is None:
            messages.append({"role": "user", "content": view.prompt})
        else:
            messages.append({"role": "user", "content": [
                {'type': 'text', 'text': view.prompt},
                self._image_content(view.image),
            ]})

        response = self.client.chat.completions.create(
            model=view.model,
            messages=messages,
            **self._build_kwargs(view.options)
        )
        return response.choices[0].message.content

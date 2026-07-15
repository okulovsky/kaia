import dataclasses
from dataclasses import dataclass
from foundation_kaia.marshalling import service, FileLike
from foundation_kaia.brainbox_utils import brainbox_endpoint


@dataclass
class OllamaOptions:
    # Sampling: how the next token is chosen.
    temperature: float|None = None  # Randomness; 0 = deterministic, higher = more random. Ollama default ~0.8.
    top_k: int|None = None  # Only sample from the K most likely next tokens.
    top_p: float|None = None  # Nucleus sampling: only sample from tokens covering this cumulative probability.
    min_p: float|None = None  # Discard tokens less likely than this fraction of the top token's probability.
    repeat_penalty: float|None = None  # Penalty applied to tokens already seen, to discourage repetition.
    repeat_last_n: int|None = None  # How many recent tokens `repeat_penalty` looks back over.
    seed: int|None = None  # Fixes the RNG for reproducible output.
    stop: list[str]|None = None  # Strings that end generation immediately when produced.

    # Mirostat: alternative sampler that targets a constant output perplexity
    # instead of using temperature/top_k/top_p directly.
    mirostat: int|None = None  # 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0.
    mirostat_tau: float|None = None  # Target perplexity ("surprise") of the output.
    mirostat_eta: float|None = None  # Learning rate: how fast Mirostat adapts towards `mirostat_tau`.

    # Output length.
    num_predict: int|None = None  # Max tokens to generate; -1 = unlimited, -2 = fill the context window.

    # Context / hardware. The model's own trained max context caps `num_ctx` regardless of this value.
    num_ctx: int|None = None  # Context window size, in tokens.
    num_gpu: int|None = None  # Number of model layers to offload to GPU.
    num_thread: int|None = None  # CPU threads to use for inference.

    # Not a sampling option: a decoding-mode switch, sent as its own top-level
    # request field rather than nested in `options` (see to_options_and_format).
    format: dict|str|None = None  # `"json"`, or a JSON Schema the output must conform to.

    def to_options_and_format(self) -> tuple[dict|None, 'dict|str|None']:
        """`format` is a top-level field in Ollama's request body, not part of `options`."""
        options = {
            f.name: getattr(self, f.name)
            for f in dataclasses.fields(self)
            if f.name != 'format' and getattr(self, f.name) is not None
        }
        return (options or None), self.format

    def __add__(self, other: 'OllamaOptions|None') -> 'OllamaOptions':
        if other is None:
            return self
        return OllamaOptions(**{
            f.name: getattr(other, f.name) if getattr(other, f.name) is not None else getattr(self, f.name)
            for f in dataclasses.fields(self)
        })

    def __radd__(self, other: None) -> 'OllamaOptions':
        if other is None:
            return self
        return NotImplemented


@service
class IOllama:
    @brainbox_endpoint
    def completions_json(self,
                          prompt: str,
                          options: OllamaOptions|None = None,
                          ) -> dict:
        ...

    @brainbox_endpoint
    def completions(self,
                     prompt: str,
                     options: OllamaOptions|None = None,
                     ) -> str:
        ...

    @brainbox_endpoint
    def question_json(self,
                      prompt: str,
                      system_prompt: str|None = None,
                      options: OllamaOptions|None = None,
                      image: FileLike|None = None,
                      ) -> dict:
        ...

    @brainbox_endpoint
    def question(self,
                 prompt: str,
                 system_prompt: str|None = None,
                 options: OllamaOptions|None = None,
                 image: FileLike|None = None,
                 ) -> str:
        ...

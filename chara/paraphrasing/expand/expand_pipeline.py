from pathlib import Path
from chara.common import ICache, FileCache, logger
from grammatron import DubParameters
from avatar.daemon import ParaphraseRecord
from ..common.value_generator import generate_values_for_template


class ExpandPipelineCache(ICache[list[str]]):
    def __init__(self, working_directory: Path | None = None):
        super().__init__(working_directory)
        self.expansion = FileCache[list[str]]()


class ExpandPipeline:
    def __init__(self, n_values: int = 3, language: str = 'ru'):
        self.n_values = n_values
        self.language = language

    def __call__(self, cache: ExpandPipelineCache, records: list[ParaphraseRecord],
                 negatives: list[str] | None = None, output_path: Path | None = None):
        @logger.phase(cache.expansion, "Expanding templates")
        def _():
            lines = []
            params = DubParameters(language=self.language)
            for record in records:
                lines.append(f"# {record.original_template_name} | {record.language}")
                try:
                    values_list = generate_values_for_template(record.template, self.n_values)
                except ValueError as e:
                    logger.log(f"Skipping {record.original_template_name}: {e}")
                    lines.append(record.filename)
                    continue
                if not values_list:
                    lines.append(record.filename)
                    continue
                for values in values_list:
                    try:
                        text = record.template.utter(values).to_str(params)
                        lines.append(text)
                    except Exception:
                        pass

            if negatives:
                lines.append(f"# __negatives__ | {self.language}")
                lines.extend(negatives)

            cache.expansion.write(lines)

        result = cache.expansion.read()
        cache.write_result(result)

        if output_path is not None:
            output_path.write_text('\n'.join(result), encoding='utf-8')
            text_lines = [l for l in result if l and not l.startswith('#')]
            logger.log(f"{len(text_lines)} lines → {output_path}")

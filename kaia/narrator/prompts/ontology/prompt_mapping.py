from typing import *
import pandas as pd
from kaia.narrator.prompts import IStringToTagsParser
from kaia.brainbox import BrainBox
from kaia.brainbox.deciders import CollectorTaskBuilder, Ollama
from dataclasses import dataclass
from yo_fluq_ds import Query

@dataclass
class PromptMapping:
    df_index_to_prompt_index: pd.DataFrame
    prompt_index_to_prompt: pd.DataFrame

    def generate_tasks(self, model: str = 'llama3.1'):
        builder = CollectorTaskBuilder()
        for row in Query.df(self.prompt_index_to_prompt):
            builder.append(
                BrainBox.Task.call(Ollama).question(row['prompt']).to_task(model),
                dict(index=row['prompt_index'])
            )
        return builder.to_collector_pack('to_array')

    def _parse(self,
              brainbox_output: list[dict],
              parser: Union[IStringToTagsParser, Callable[[str], List[Dict]]],
              error_field: str|None = None
              ):
        if isinstance(parser, IStringToTagsParser):
            parser = parser.parse
        elif callable(parser):
            pass
        else:
            raise ValueError(f"Parser expected to be IStringToTagsParser or callable, but was {parser}")

        output = []
        for brainbox_item in brainbox_output:
            pindex = brainbox_item['tags']['index']
            if brainbox_item['result'] is None:
                if error_field is not None:
                    output.append({'prompt_index': pindex, error_field: brainbox_item['error']})
                continue
            try:
                parse_results = parser(brainbox_item['result'])
            except Exception as ex:
                if error_field is not None:
                    output.append({'prompt_index': pindex, error_field: str(ex)})
                continue
            for parse_result in parse_results:
                parse_result['prompt_index'] = pindex
                output.append(parse_result)

        return pd.DataFrame(output)

    def _get_prompt_merge(self, parsed_df):
        df = self.df_index_to_prompt_index
        df = df.merge(
            parsed_df,
            left_on='prompt_index',
            right_on='prompt_index'
        )
        return df

    def _merge(self, original_df, parsed_df):
        df = original_df.merge(
            self._get_prompt_merge(parsed_df),
            left_index=True,
            right_on='original_index')
        return df

    def apply(self,
                brainbox_output,
                parser: IStringToTagsParser,
                original_df: pd.DataFrame,
                error_field: str|None = 'error',
                drop_intermediate_columns=True
                ):
        df = self._merge(
            original_df,
            self._parse(
                brainbox_output,
                parser,
                error_field
            )
        )
        if drop_intermediate_columns:
            df = df.drop(['original_index', 'prompt_index'], axis=1)
        return df


    @staticmethod
    def compute(
            df: pd.DataFrame,
            prompt_generation: Callable[[Dict], str],
            skip_repeating_prompts: bool = True,
    ):
        prompt_to_index_dict = dict()
        prompt_to_index = []
        df_index_to_prompt_index = []

        for index, tags in zip(df.index, Query.df(df)):
            prompt = prompt_generation(tags)
            prompt_index = index
            if skip_repeating_prompts:
                if prompt not in prompt_to_index_dict:
                    idx = len(prompt_to_index_dict)
                    prompt_to_index_dict[prompt] = idx
                prompt_index = prompt_to_index_dict[prompt]
            prompt_to_index.append(dict(prompt_index=prompt_index, prompt=prompt))
            df_index_to_prompt_index.append(dict(original_index=index, prompt_index=prompt_index))

        return PromptMapping(
            pd.DataFrame(df_index_to_prompt_index),
            pd.DataFrame(prompt_to_index)
        )




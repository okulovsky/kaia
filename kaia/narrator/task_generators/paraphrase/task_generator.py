import uuid
from typing import *
from ....dub.core import Template, PredefinedField, ParaphraseInfo
from ...prompts import Character, World, Prompt
from kaia.brainbox.deciders import CollectorTaskBuilder
from kaia.brainbox import BrainBoxTask
from copy import deepcopy
from ...prompts import Conventions
from enum import Enum
import numpy


class TaskGenerator:
    story_field = PredefinedField('story')
    prompt_type_field = PredefinedField('prompt_type')
    template_field = 'paraphrase_for_template'
    utterance_in_story_field = PredefinedField("utterance_in_story")
    DEFAULT_DIALOG_LINE_TO_STORY_TEMPLATE = Template(f'{World.user} says, "{utterance_in_story_field}"')

    class PromptType(Enum):
        Instead = 0
        After = 1
        StoryInstead = 2

    def _convert_tag_argument(self, argument) -> dict[str, Any]:
        result = {}
        if isinstance(argument, Mapping):
            for k, v in argument.items():
                if not isinstance(k, str):
                    raise ValueError("If tag argument is dict, keys must be strings")
                result[k] = v
        else:
            for k in argument:
                if not isinstance(k, str):
                    raise ValueError("If tag argument is iterable, all items must be strings")
                result[k] = k
        return result

    def __init__(self,
                 task_factory:Callable[[str, dict], BrainBoxTask],
                 prompt: Prompt,
                 templates: Iterable[Template],
                 users: Iterable[str],
                 additional_tag_fields: dict[str,Iterable],
                 dialog_line_to_story_template: None|Template = None,
        ):
        self.task_factory = task_factory
        self.prompt = prompt
        self.templates = templates
        self.tag_fields: dict[str, dict[str, Any]] = {}
        self.tag_fields[World.user.field_name] = self._convert_tag_argument(users)
        for k, v in additional_tag_fields.items():
            self.tag_fields[k] = self._convert_tag_argument(v)

        if dialog_line_to_story_template is None:
            dialog_line_to_story_template = TaskGenerator.DEFAULT_DIALOG_LINE_TO_STORY_TEMPLATE
        self.dialog_line_to_story_template = dialog_line_to_story_template


    def get_story(self, data, template: Template, user: Character):
        if template.meta.paraphrase is None:
            raise ValueError("Paraphrase not available")
        if template.meta.paraphrase.as_story:
            previous = template.meta.reply_to
            if previous is None:
                raise ValueError(f"Template {template.name} has `story` paraphrase, but doesn't have `reply_to` metadata set")
            try:
                utterance = previous().to_str()
            except Exception as e:
                raise ValueError(f"Teplate {template.name} refers to {previous.name} is a story, but the reffered template cannot be uttered without parameters")
            return self.dialog_line_to_story_template.utter(**{
                World.user.field_name: user,
                TaskGenerator.utterance_in_story_field.get_name():utterance
            }).to_str()
        if template.meta.paraphrase.description is not None:
            return Template.free(template.meta.paraphrase.description).to_str(data)

        raise ValueError(f"Can't produce story for template {template.name}")

    def get_prompt_type(self, template: Template):
        if template.meta.paraphrase is None:
            raise ValueError("Paraphrase not available")
        if template.meta.paraphrase.as_story:
            if template.meta.paraphrase.type == ParaphraseInfo.Type.Instead:
                return TaskGenerator.PromptType.StoryInstead
            else:
                raise ValueError(
                    f"Error in template {template.name}: Not imlemented for as_style=True and paraphrase type {template.meta.paraphrase.type}"
                )
        else:
            if template.meta.paraphrase.type == ParaphraseInfo.Type.Instead:
                return TaskGenerator.PromptType.Instead
            elif template.meta.paraphrase.type == ParaphraseInfo.Type.After:
                return TaskGenerator.PromptType.After
            else:
                raise ValueError(f"Error in template {template.name}: unknown paraphrase type {template.meta.paraphrase.Type}")

    def _get_grid(self) -> tuple[list[Template], list[dict]]:
        from yo_fluq_ds import Query
        templates = [t for t in self.templates if t.meta.paraphrase is not None]
        grid_data = {key: list(value) for key, value in self.tag_fields.items()}
        tag_grid = list(Query.combinatorics.grid(**grid_data))
        return templates, tag_grid


    def _to_task(self, template, raw_tags)->tuple[BrainBoxTask,dict]:
        tags = deepcopy(raw_tags)
        tags[Conventions.template_to_paraphrase_tag_name] = template.name

        story_items = {}
        for k, v in raw_tags.items():
            story_items[k] = self.tag_fields[k][v]

        story_items[TaskGenerator.story_field.get_name()] = self.get_story(
            story_items,
            template,
            story_items[World.user.field_name]
        )
        story_items[TaskGenerator.prompt_type_field.get_name()] = self.get_prompt_type(template)
        value = self.prompt.compute_last_value(story_items)
        return self.task_factory(value, tags), tags

    def generate_random_task(self):
        templates, tag_grid = self._get_grid()
        template = templates[numpy.random.randint(len(templates))]
        raw_tags = tag_grid[numpy.random.randint(len(tag_grid))]
        task, _ = self._to_task(template, raw_tags)
        return task

    def generate(self):
        from yo_fluq_ds import Query, fluq
        templates, tag_grid = self._get_grid()

        builder = CollectorTaskBuilder()

        for template in Query.en(templates).feed(fluq.with_progress_bar()):
            for raw_tags in tag_grid:
                task, tags = self._to_task(template, raw_tags)
                builder.append(task, tags)

        return builder


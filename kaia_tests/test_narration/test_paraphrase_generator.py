from kaia.brainbox import BrainBoxTask
from kaia.brainbox.deciders import FakeLLMDecider
from kaia.narrator.task_generators import ParaphraseTaskGenerator
from kaia.narrator import World, Character, Prompt
from kaia.dub import Template, PredefinedField
from unittest import TestCase


def task_factory(prompt, tags):
    return BrainBoxTask.call(FakeLLMDecider)(prompt=prompt)

def get_df(template):
    characters = [Character('character_0', Character.Gender.Feminine),
                  Character('character_1', Character.Gender.Masculine)]
    characters = {c.name: c for c in characters}

    users = [Character('user_0', Character.Gender.Feminine), Character('user_1', Character.Gender.Masculine)]
    users = {u.name: u for u in users}

    resulting_template = Template.free(f'{World.user}/{World.character}/{ParaphraseTaskGenerator.prompt_type_field}/{ParaphraseTaskGenerator.story_field}')
    prompt = (
        Prompt()
        .add_binding('result', resulting_template)
    )
    generator = ParaphraseTaskGenerator(
        task_factory,
        prompt,
        [template],
        users,
        {World.character.field_name: characters}
    )
    builder = generator.create_builder()
    return builder.to_debug_df().sort_values('prompt')



class ParaphraseTaskGeneratorTestCase(TestCase):

    def normal_checks(self, df, template_name):
        self.assertListEqual(
            ['user_0', 'user_0', 'user_1', 'user_1'],
            list(df.user)
        )
        self.assertListEqual(
            ['character_0', 'character_1', 'character_0', 'character_1'],
            list(df.character)
        )
        self.assertListEqual(
            [template_name] * 4,
            list(df.template_to_paraphrase)
        )


    def test_after(self):
        df = get_df(
            Template("After").paraphrase.after('Paraphrase after').with_name('template_after')
        )

        self.assertListEqual(
            ['user_0/character_0/PromptType.After/Paraphrase after',
             'user_0/character_1/PromptType.After/Paraphrase after',
             'user_1/character_0/PromptType.After/Paraphrase after',
             'user_1/character_1/PromptType.After/Paraphrase after'],
            list(df.prompt)
        )

        self.normal_checks(df, 'template_after')

    def test_instead(self):
        df = get_df(
            Template("Instead").paraphrase('Paraphrase instead').with_name('template_instead')
        )

        self.assertListEqual(
            ['user_0/character_0/PromptType.Instead/Paraphrase instead',
             'user_0/character_1/PromptType.Instead/Paraphrase instead',
             'user_1/character_0/PromptType.Instead/Paraphrase instead',
             'user_1/character_1/PromptType.Instead/Paraphrase instead'],
            list(df.prompt)
        )
        self.normal_checks(df, 'template_instead')


    def test_story(self):
        df = get_df(
            Template("Instead").paraphrase.story().with_name('template_story').meta.set(
                reply_to=Template("Story")
            )
        )
        self.assertListEqual(
            ['user_0/character_0/PromptType.StoryInstead/user_0 says, "Story"',
             'user_0/character_1/PromptType.StoryInstead/user_0 says, "Story"',
             'user_1/character_0/PromptType.StoryInstead/user_1 says, "Story"',
             'user_1/character_1/PromptType.StoryInstead/user_1 says, "Story"'],
            list(df.prompt)
        )
        self.normal_checks(df, 'template_story')

    def test_with_fields_inside_story(self):
        df = get_df(
            Template("Fields").paraphrase(f'{World.user}+{World.character}').with_name('template_fields')
        )
        self.assertListEqual(
            ['user_0/character_0/PromptType.Instead/user_0+character_0',
             'user_0/character_1/PromptType.Instead/user_0+character_1',
             'user_1/character_0/PromptType.Instead/user_1+character_0',
             'user_1/character_1/PromptType.Instead/user_1+character_1'],
            list(df.prompt)
        )
        self.normal_checks(df, 'template_fields')


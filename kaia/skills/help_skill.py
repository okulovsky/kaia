from typing import *
from kaia import IKaiaSkill, SingleLineKaiaSkill, ChatCommand
from grammatron import *

class HelpIntents(TemplatesCollection):
    help = Template("What can you do?")

class HelpReplies(TemplatesCollection):
    help = (
        Template("Here is the list of available commands")
        .no_paraphrasing()
    )

class HelpBuilder(TemplateParserBase):
    def __init__(self):
        self.buffer = []

    def open_template(self, template_index: int, template: Template, total_templates: int) -> bool:
        if template_index!=0:
            self.buffer.append('\n')
        return True

    def open_language(self, language_index: int, language: str, template_dub: TemplateDub, total_languages: int) -> bool:
        return language=='en'

    def open_sequence(self, sequence_index: int, sequence: SequenceDub, total_sequences: int) -> bool:
        if sequence_index!=0:
            self.buffer.append(', ')
        return True

    def on_leaf(self, leaf_info: TemplateParserBase.LeafInfo) -> None:
        if leaf_info.constant is not None:
            self.buffer.append(leaf_info.constant.value)
        elif leaf_info.grammar_adoptable is not None:
            self.buffer.append(leaf_info.grammar_adoptable.value)
        else:
            self.buffer.append('{'+leaf_info.variable.name+'}')



class HelpSkill(SingleLineKaiaSkill):
    def __init__(self, skills: Iterable[IKaiaSkill]|None = None):
        self.skills = skills
        super().__init__(HelpIntents, HelpReplies)


    def run(self):
        if self.skills is None:
            raise ValueError("Skill is misconfigured, no skills are provided")
        builder = HelpBuilder()
        for skill in self.skills:
            if len(builder.buffer) != 0:
                builder.buffer.append('\n\n')
            builder.buffer.append(f'<b>{skill.get_name()}</b>\n')
            builder.parse(skill.get_intents())
        yield ChatCommand(''.join(builder.buffer), ChatCommand.MessageType.to_user)
        yield HelpReplies.help.utter()




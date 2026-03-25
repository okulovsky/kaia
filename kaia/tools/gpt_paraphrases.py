from chara.paraphrasing.intents import IntentCaseBuilder, IntentPrompter
from kaia.skills.timer_skill import TimerIntents
from kaia.skills.time import TimeIntents
from kaia.skills.date import DateIntents

all_templates = [
    *TimerIntents.get_templates(),
    *TimeIntents.get_templates(),
    *DateIntents.get_templates(),
]


def build_prompts(languages=('ru',)):
    builder = IntentCaseBuilder(templates=all_templates, languages=languages)
    prompter = IntentPrompter()
    cases = builder.create_cases()
    return [(case, prompter(case)) for case in cases]


if __name__ == '__main__':
    items = build_prompts()
    print(f"Total prompts: {len(items)}")
    for case, prompt in items:
        modality = case.modality.name if case.modality else 'no modality'
        print(f"\n--- {case.template.template.get_name()} / {modality} ---")
        print(prompt)

from kaia.avatar.dub.languages.en import *

class NutritionIntents(TemplatesCollection):
    eaten = Template()
    wrong = Template()
    yes = Template()
    finished = Template()


class NutritionReplies(TemplatesCollection):
    eaten_confirm = Template(
        '{food}, {amount}.',
        '{food}, {amount} of {unit}{s}.',
        food = IdentityDub(),
        amount = CardinalDub(0, 1000),
        unit = IdentityDub(),
        s = PluralAgreement('amount','', 's')
    )

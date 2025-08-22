from unittest import TestCase

def make(test_case: TestCase):
    from grammatron import Template, VariableDub, CardinalDub, PluralAgreement

    AMOUNT = VariableDub("amount", CardinalDub())

    template = Template(
        f"You've got {PluralAgreement(AMOUNT, "message")}"
    )


from unittest import TestCase

def make(test_case: TestCase):
    from grammatron import Template, VariableDub, CardinalDub
    from grammatron import PluralAgreement

    AMOUNT = VariableDub("amount", CardinalDub())

    template = Template(
        f"You've got {PluralAgreement(AMOUNT, "message")}"
    )

    test_case.assertEqual(
        "You've got one message",
        template(1).to_str()
    )

    test_case.assertEqual(
        "You've got two messages",
        template(2).to_str()
    )

    from grammatron import OptionsDub

    ITEM = VariableDub("item", OptionsDub(['car','bike','truck']))

    template = Template(
        f"You've ordered {PluralAgreement(AMOUNT, ITEM)}"
    )

    test_case.assertEqual(
        "You've ordered two cars",
        template.utter(AMOUNT.assign(2), ITEM.assign('car')).to_str()
    )

    test_case.assertEqual(
        "You've ordered one bike",
        template.utter(AMOUNT.assign(1), ITEM.assign('bike')).to_str()
    )







if __name__ == '__main__':
    test = TestCase()
    make(test)
from unittest import TestCase

def make(test_case: TestCase):
    from grammatron import Template, VariableDub, CardinalDub

    AMOUNT = VariableDub("amount", CardinalDub())

    template = Template(
        f"You've got {AMOUNT} messages"
    )

    utterance = template.utter(2)

    test_case.assertEqual(
        "You've got two messages",
        utterance.to_str()
    )

    test_case.assertEqual(
        "You've got three messages",
        template(3).to_str()
    )

    from grammatron import DubParameters

    test_case.assertEqual(
        "You've got 3 messages",
        template(3).to_str(DubParameters(spoken=False))
    )

    UNREAD = VariableDub("unread", CardinalDub())

    template = Template(
        f"You've got {AMOUNT} messages, {UNREAD} unread"
    )

    test_case.assertEqual(
        "You've got two messages, one unread",
        template(AMOUNT.assign(2), UNREAD.assign(1)).to_str()
    )

    test_case.assertEqual(
        "You've got two messages, one unread",
        template(amount = 2, unread = 1).to_str()
    )

    from dataclasses import dataclass

    @dataclass
    class Data:
        amount: int
        unread: int

    template = Template(
        f"You've got {AMOUNT} messages, {UNREAD} unread"
    ).with_type(Data)

    test_case.assertEqual(
        "You've got two messages, one unread",
        template(Data(amount = 2, unread = 1)).to_str()
    )














if __name__ == '__main__':
    test = TestCase()
    make(test)
import datetime
from unittest import TestCase

def make(test_case: TestCase):
    from grammatron import VariableDub, Template, OptionsDub
    from enum import Enum


    class PaymentMethod(Enum):
        credit_card = 0
        paypal = "Paypal"


    METHOD = VariableDub("method", OptionsDub(PaymentMethod))

    template = Template(f"Your payment method is {METHOD}")

    test_case.assertEqual(
        "Your payment method is credit card",
        template.to_str(PaymentMethod.credit_card)
    )

    test_case.assertEqual(
        "Your payment method is Paypal",
        template.to_str(PaymentMethod.paypal)
    )

    from grammatron import DateDub

    template = Template(f"Today is {DateDub().as_variable('date')}")

    test_case.assertEqual(
        "Today is January, first, fifteenth",
        template.to_str(datetime.datetime(2015, 1, 1))
    )




if __name__ == '__main__':
    test = TestCase()
    make(test)
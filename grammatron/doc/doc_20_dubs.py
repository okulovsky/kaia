from foundation_kaia.releasing.mddoc import *

expected_cc = ControlValue.mddoc_define_control_value("Your payment method is credit card")
expected_pp = ControlValue.mddoc_define_control_value("Your payment method is Paypal")
expected_date = ControlValue.mddoc_define_control_value("Today is January, first, fifteenth")
expected_time = ControlValue.mddoc_define_control_value("Now is fifteen hours and twenty-three minutes")

if __name__ == '__main__':

    """
    ## Dubs

    A *dub* describes how to convert a value of certain type to a spoken and written string.
    Several built-in dubs are available.

    ### OptionsDub

    `OptionsDub` maps enum members (or plain strings) to their human-readable forms.
    Enum names with underscores are automatically converted to space-separated words:
    """

    from grammatron import VariableDub, Template, OptionsDub
    from enum import Enum

    class PaymentMethod(Enum):
        credit_card = 0
        paypal = "Paypal"

    METHOD = VariableDub("method", OptionsDub(PaymentMethod))
    template = Template(f"Your payment method is {METHOD}")

    credit_card = template.to_str(PaymentMethod.credit_card)
    paypal = template.to_str(PaymentMethod.paypal)

    """
    `credit_card` will be:
    """

    expected_cc.mddoc_validate_control_value(credit_card)

    """
    And for `paypal`:
    """

    expected_pp.mddoc_validate_control_value(paypal)

    """
    ### DateDub

    `DateDub` converts a `datetime` to its spoken form.
    Use `.as_variable(name)` as a shorthand for wrapping in a `VariableDub`:
    """

    import datetime
    from grammatron import DateDub

    template = Template(f"Today is {DateDub().as_variable('date')}")
    result = template.to_str(datetime.datetime(2015, 1, 1))

    """
    `result` will be:
    """

    expected_date.mddoc_validate_control_value(result)

    """
    ### TimedeltaDub
    
    """

    from grammatron import TimedeltaDub

    template = Template(f"Now is {TimedeltaDub().as_variable('time')}")
    result = template.to_str(datetime.timedelta(hours=15, minutes = 23))

    """
    `result` will be:
    """

    expected_time.mddoc_validate_control_value(result)

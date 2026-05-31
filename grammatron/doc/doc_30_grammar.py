from foundation_kaia.releasing.mddoc import *

expected_one = ControlValue.mddoc_define_control_value("You've got one message")
expected_two = ControlValue.mddoc_define_control_value("You've got two messages")
expected_cars = ControlValue.mddoc_define_control_value("You've ordered two cars")
expected_bike = ControlValue.mddoc_define_control_value("You've ordered one bike")
expected_juice = ControlValue.mddoc_define_control_value("You've ordered two big glasses of juice")
expected_juice_wrong = ControlValue.mddoc_define_control_value("You've ordered two smalls glass of juice")

if __name__ == '__main__':

    """
    ## Grammar

    ### PluralAgreement

    `PluralAgreement` wraps a numeric dub and a noun, producing the correctly inflected form:
    """

    from grammatron import Template, VariableDub, CardinalDub, PluralAgreement

    AMOUNT = VariableDub("amount", CardinalDub())
    template = Template(f"You've got {PluralAgreement(AMOUNT, 'message')}")

    result = template(1).to_str()

    """
    `result` will be:
    """

    expected_one.mddoc_validate_control_value(result)

    result = template(2).to_str()

    """
    And for 2:
    """

    expected_two.mddoc_validate_control_value(result)

    """
    The noun argument can itself be a dub — the plural form of the chosen option is then used:
    """

    from grammatron import OptionsDub

    ITEM = VariableDub("item", OptionsDub(['car', 'bike', 'truck']))
    template = Template(f"You've ordered {PluralAgreement(AMOUNT, ITEM)}")

    cars = template.utter(AMOUNT.assign(2), ITEM.assign('car')).to_str()
    bikes = template.utter(AMOUNT.assign(1), ITEM.assign('bike')).to_str()

    """
    `cars` will be:
    """

    expected_cars.mddoc_validate_control_value(cars)

    """
    And for one bike:
    """

    expected_bike.mddoc_validate_control_value(bikes)

    """
    I will also work in fairly complicated cases:
    """

    AMOUNT = VariableDub("amount", CardinalDub())
    template = Template(f"You've ordered {PluralAgreement(AMOUNT, 'big glass of juice')}")
    result = template(2).to_str()

    """
    The result will be:
    """

    expected_juice.mddoc_validate_control_value(result)

    """
    However, this is not perfect:
    
    """
    template = Template(f"You've ordered {PluralAgreement(AMOUNT, 'small glass of juice')}")
    result = template(2).to_str()

    """
    The result will be:
    """

    expected_juice_wrong.mddoc_validate_control_value(result)

    """
    This happens because "small" can be used as the noun in English.
    """


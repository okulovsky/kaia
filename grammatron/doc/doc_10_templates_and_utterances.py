from foundation_kaia.releasing.mddoc import *

expected_basic = ControlValue.mddoc_define_control_value("You've got two messages")
expected_numeric = ControlValue.mddoc_define_control_value("You've got 3 messages")
expected_multi = ControlValue.mddoc_define_control_value("You've got two messages, one unread")

if __name__ == '__main__':

    """
    # grammatron
    
    `grammatron` is a library for producing natural-language utterances from templates.
    Instead of raw f-strings, templates use typed *dubs* (dubbing units) that convert
    values into spoken-style text. Grammatron ensures the grammatical coherence of the
    generated text in the supported languages, which are English, German and Russian.
    
    ## Templates and Utterances
    
    A `Template` is built from an f-string that embeds `VariableDub` placeholders.
    `CardinalDub` converts integers to their spoken form:
    """

    from grammatron import Template, VariableDub, CardinalDub, DubParameters

    AMOUNT = VariableDub("amount", CardinalDub())

    template = Template(f"You've got {AMOUNT} messages")

    """
    Calling `template.utter(value)` (or the shorthand `template(value)`) produces an `Utterance`.
    Call `.to_str()` to get the final string:
    """

    result = template.utter(2).to_str()

    """
    The result will be:
    """
    expected_basic.mddoc_validate_control_value(result)

    """
    Pass `DubParameters(spoken=False)` to get the numeric form instead:
    """
    result = template(3).to_str(DubParameters(spoken=False))

    """
    `result` will be:
    """

    expected_numeric.mddoc_validate_control_value(result)

    """
    ### Multiple variables
    
    When a template has several dubs, pass assignments explicitly:
    """

    UNREAD = VariableDub("unread", CardinalDub())

    template = Template(f"You've got {AMOUNT} messages, {UNREAD} unread")
    result = template(AMOUNT.assign(2), UNREAD.assign(1)).to_str()

    """
    The result will be:
    """
    expected_multi.mddoc_validate_control_value(result)

    """
    Keyword arguments are also supported:
    """

    result = template(amount=2, unread=1).to_str()

    """
    The result will be:
    """

    expected_multi.mddoc_validate_control_value(result)


    """
    ### Typed templates
    
    Bind the template to a dataclass with `.with_type()` so a single object can be passed:
    """

    from dataclasses import dataclass

    @dataclass
    class Data:
        amount: int
        unread: int

    typed_template = Template(f"You've got {AMOUNT} messages, {UNREAD} unread").with_type(Data)

    result = typed_template(Data(amount=2, unread=1)).to_str()

    """
    The result will be:
    """
    expected_multi.mddoc_validate_control_value(result)

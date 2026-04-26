import datetime

from foundation_kaia.releasing.mddoc import *

german = ControlValue.mddoc_define_control_value(['Ich trage einen kleinen Koffer', 'Ich fahre mit einem kleinen Koffer', 'Ich trage eine kleine Tasche', 'Ich fahre mit einer kleinen Tasche', 'Ich trage zwei kleine Koffer', 'Ich fahre mit zwei kleinen Koffern', 'Ich trage zwei kleine Taschen', 'Ich fahre mit zwei kleinen Taschen'])
multi = ControlValue.mddoc_define_control_value(['It is three hours and forty-five minutes', 'Es ist drei Stunden und fünfundvierzig Minuten', 'Сейчас три часа и сорок пять минут'])

if __name__ == '__main__':
    """
    
    ### German and Russian support
    
    In germanic and slavic languages, this is more complicated: 
    
    | English | German | Russian | 
    --
    I carry one small suitcase | Ich trage einen kleinen Koffer | Я несу один маленький чемодан
    I travel with one small suitcase | Ich fahre mit einem kleinen Koffer | Я еду с одним маленьким чемоданом
    I carry one small bag | Ich trage eine kleine Tasche | Я несу одну маленькую сумку
    I travel with one small bag | Ich fahre mit einer kleinen Tasche | Я еду с одной маленькой сумкой
    I carry two small suitcases | Ich trage zwei kleine Koffer | Я несу два маленьких чемодана 
    I travel with two small suitcases | Ich fahre mit zwei kleinen Koffern | Я еду с двумя маленькими чемоданами
    I carry two small bags | Ich trage zwei kleine Taschen | Я несу одну маленькую сумку
    I traver with two small bags | Ich fahre mit zwei kleinen Taschen | Я еду с двумя маленькими сумками
    
    So, to put correctly together a number and "kleine Tasche/klein Koffer" or "маленькая сумка/маленький чемодан", one must take into account:
    * The case of the noun group ("tragen" and "нести" requires accusative, "fahre mit" - dative, "ехать" - prepositional case)
    * The genus of the noun (Koffer and чемодан are mascular, Tasche and сумка are feminar, neutrum is also possible)
    * The value of the numeral
    
    These parameters determine the form of noun, adjective and the numeral. 
    And this is not something you may ignore: natives see these errors instantly, and their impression of the product declines.
    
    `grammatron` takes case of that too (but may fail in some cases, as it was with English):
    
    """

    from grammatron import CardinalDub, PluralAgreement, OptionsDub, Template, DubParameters
    from grammatron.grammars.de import DeCasus
    from enum import Enum

    class GermanOptions(Enum):
        bag = "kleine Tasche"
        suitcase = "klein Koffer"

    AMOUNT = CardinalDub().as_variable("amount")
    OBJECT = OptionsDub(GermanOptions).as_variable("object")
    carry_template = Template(f"Ich trage {PluralAgreement(AMOUNT, OBJECT).grammar.de(casus=DeCasus.AKKUSATIV)}")
    travel_template = Template(f"Ich fahre mit {PluralAgreement(AMOUNT, OBJECT).grammar.de(casus=DeCasus.DATIV)}")

    results = [
        template.utter(amount = amount, object = object).to_str(DubParameters(language='de'))
        for amount in [1,2]
        for object in [GermanOptions.suitcase, GermanOptions.bag]
        for template in [carry_template, travel_template]
    ]

    """
    The results will be, as in the table above:
    """

    german.mddoc_validate_control_value(results)

    """
    For russian:
    """

    from grammatron.grammars.ru import RuCase

    class RussianOptions(Enum):
        bag = "маленькая сумка"
        suitcase = "маленький чемодан"


    AMOUNT = CardinalDub().as_variable("amount")
    OBJECT = OptionsDub(RussianOptions).as_variable("object")
    carry_template = Template(f"Я несу {PluralAgreement(AMOUNT, OBJECT).grammar.ru(case=RuCase.ACCUSATIVE)}")
    travel_template = Template(f"Я еду с {PluralAgreement(AMOUNT, OBJECT).grammar.ru(case=RuCase.INSTRUMENTAL)}")

    results = [
        template.utter(amount = amount, object = object).to_str(DubParameters(language='ru'))
        for amount in [1,2]
        for object in [RussianOptions.suitcase, RussianOptions.bag]
        for template in [carry_template, travel_template]
    ]

    print(results)

    """
    ### Multi-language templates
    
    It is possible to declare multi-language templates:
    
    """
    from grammatron import TimedeltaDub
    TIME = TimedeltaDub().as_variable("time")
    template = Template(
        f"It is {TIME}",
        de = f"Es ist {TIME}",
        ru = f"Сейчас {TIME}"
    )
    results = [
        template.utter(datetime.timedelta(hours=3,minutes=45)).to_str(DubParameters(language=language))
        for language in ['en', 'de', 'ru']
    ]

    """
    The results array is:
    """

    multi.mddoc_validate_control_value(results)

    """
    Currently, this path is not well-explored, e.g., it's not compatible with OptionsDub.
    Kaia evolved more in the direction where the LLM produces the translations to the different languages
    instead of programmers writing them manually, so this branch of multi-language templates is unlikely to be resumed.
    
    """











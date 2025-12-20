from dataclasses import dataclass
from grammatron import DataclassTemplateDub, VariableDub, CardinalDub, ToStrDub, PluralAgreement, GrammarAdoptableDub



@dataclass
class RecipeReminder:
    delay_in_minutes: float
    announcement: str
    label: str|None = None



@dataclass
class RecipeStep:
    main_text: str
    reminders: tuple[RecipeReminder, ...] = ()


@dataclass
class RecipeIngredient:
    name: str
    grams: int|None = None
    amount: int | None = None
    unit: str|None = None


    @staticmethod
    def template():
        NAME = ToStrDub().as_variable("name")
        GRAMS = CardinalDub().as_variable("grams")
        UNIT = ToStrDub().as_variable("unit")
        AMOUNT = CardinalDub().as_variable("amount")

        return DataclassTemplateDub(
            RecipeIngredient,
            f"{NAME}",
            f"A {UNIT} of {NAME}",
            f"{PluralAgreement(AMOUNT, UNIT)} of {NAME}",
            f"{NAME} ({PluralAgreement(GRAMS, 'gram')})",
            f"A {UNIT} of {NAME} ({PluralAgreement(GRAMS, 'gram')})",
            f"{PluralAgreement(AMOUNT, UNIT)} of {NAME} ({PluralAgreement(GRAMS, 'gram')})",
        )


@dataclass
class Recipe:
    dish: str
    steps: tuple[RecipeStep,...]
    ingredients: tuple[RecipeIngredient,...]

    Step = RecipeStep
    Reminder = RecipeReminder
    Ingredient = RecipeIngredient

    @staticmethod
    def define(
            name: str,
            *components: str|dict[int,str]|RecipeIngredient
    ):
        ingredients = []
        steps = []
        for component in components:
            if isinstance(component, str):
                steps.append(RecipeStep(component))
            elif isinstance(component, dict):
                reminders = []
                for delay, announcement in component.items():
                    reminders.append(RecipeReminder(delay, announcement))
                if len(steps) == 0:
                    raise ValueError("Before reminder, there must be a step it is attached to")
                steps[-1].reminders = reminders
            elif isinstance(component, RecipeIngredient):
                ingredients.append(component)
        return Recipe(
            name,
            tuple(steps),
            tuple(ingredients)
        )



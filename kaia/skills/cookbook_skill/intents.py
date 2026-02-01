from grammatron import *
from kaia import World

DISH = VariableDub(
    "dish",
    description="one of the dish in the cookbook"
)

MINUTES = VariableDub(
    "minutes",
    description="the duration of the set timer, in minutes"
)

class CookBookIntents(TemplatesCollection):
    recipe_book = Template("Recipe book")
    recipe = Template(f"How to cook {DISH}")
    ingredients = Template(f"Send me ingredients for {DISH}")
    next_step = Template("Next step")
    cancel = Template("Cancel the recipe")


class CookBookReplies(TemplatesCollection):
    busy = (
        Template(f"We're already busy with {DISH}, cannot start a new recipe")
        .context(f"{World.user} asks to start a new recipe, but there is currently another one in progress, so it's not possible")
    )

    no_recipe = (
        Template(f"Can't find a recipe for {DISH}")
        .no_paraphrasing()
    )

    no_ingredients = (
        Template(f'No ingridients are available for {DISH}')
        .context(f"{World.user} asks for the ingredients for a particular recipe, but they are not recorded.")
    )

    next_timer_in = (
        Template(f"The next timer will elapse in {PluralAgreement(MINUTES, 'minutes')}")
        .context(f"{World.character} guides {World.user} through a cookbook recipe, there are still additional steps to do after some time, and {World.character} informs {World.user} when the nearest one happen.")
    )

    recipe_is_cancelled = (
        Template(f"The recipe is cancelled.")
        .context(f"{World.user} requested to stop the recipe")
    )

    all_done = (
        Template("All done!")
        .context(f"{World.character} informs {World.user} that the cookbook recipe has been completed")
    )

    pick_recipe = (
        Template("Pick a recipe from a cookbook!")
        .context(f"{World.character} offers {World.user} to pick a recipe from the cookbook, so they would cook together")
    )



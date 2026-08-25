from creative_articulator.drama.data import IDiff
from creative_articulator.drama.driver import StoryDriver


def run_generation(driver: StoryDriver) -> list:
    """
    Drains one call to `driver.generate()`, applying every yielded IDiff to
    `driver.story` along the way -- mirroring what ChatService._process_diff
    does in production. Without this, the story's state never advances and
    the engines would keep re-generating from the same (stale) state.
    """
    results = []
    for output in driver.generate():
        if isinstance(output, IDiff):
            output.apply(driver.story)
        results.append(output)
    return results

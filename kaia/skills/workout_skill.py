from dataclasses import dataclass
from kaia.assistant import KaiaSkillBase, CommonIntents
from grammatron import *
from kaia import  TickEvent, World
from eaglesong import Listen, Return
from typing import cast
from yo_fluq import Query
from datetime import timedelta
from .music_skill import IMusicPlayer

@dataclass
class Excercise:
    name: str
    duration_in_seconds: int
    rest_afterwards_in_seconds: int|None

@dataclass
class Workout:
    name: str
    items: list[Excercise]

DURATION = VariableDub(
    'duration',
    TimedeltaDub(True, True, True),
    'the duration of the exercise or the rest afterwards'
)

WORKOUT_NAME = VariableDub(
    'workout_name',
    description='Workout name, e.g. "boxing" or "stretching"'
)

EXERCISE = VariableDub(
    "exercise",
    description="One of the exercises in the workout, e.g. 'burpies', 'squats' etc"
)

class WorkoutIntents(TemplatesCollection):
    start = Template(f"Let's do {WORKOUT_NAME} workout!")

class WorkoutReplies(TemplatesCollection):
    starting = Template(f"Okay, starting training {WORKOUT_NAME}")
    exercise = Template(f"Now doing {EXERCISE} for {DURATION}")
    workout_not_found = Template("Workout not found").context(f"{World.user} asks for a workout that is not in the list")
    keep_going = Template("Keep going!", "You're going great!").context(f"{World.character} runs a workout for {World.user}, and encourages {World.user.pronoun.objective} during the exercise")
    almost_there = Template("Almost there!", "Almost done").context(f"{World.character} runs a workout for {World.user}, and tells {World.user.pronoun.objective} that the exercise is almost completed")
    rest = Template(f"Now rest for {DURATION}").context(f"{World.character} runs a workout for {World.user}, and tells {World.user.pronoun.objective} that it is time to rest")
    done = Template("The workout is done! Good job!").context(f"{World.user} completed the workout routine that {World.character} was running")
    cancelled = Template("The workout is cancelled").context(f"{World.user} requested to stop the workout routing thet {World.character} was running")

class WorkoutSkill(KaiaSkillBase):
    def __init__(self, workouts: list[Workout], music: IMusicPlayer|None, last_announcement_skip: int = 10):
        self.workouts = workouts
        self.music = music
        workout_names = [w.name for w in workouts]
        self.last_announcement_skip = last_announcement_skip
        super().__init__(
            [WorkoutIntents.start.substitute(workout_name=OptionsDub(workout_names))],
            WorkoutReplies,
        )

    def should_start(self, input) -> bool:
        return input in WorkoutIntents.start

    def should_proceed(self, input) -> bool:
        return isinstance(input, TickEvent) or input in CommonIntents.stop

    def _wait(self, seconds: int):
        print(f'Now waiting for {seconds}')
        first_tick: TickEvent|None = None
        while True:
            tick = yield Listen()
            if tick in CommonIntents.stop:
                yield WorkoutReplies.cancelled()
                raise Return()
            tick = cast(TickEvent, tick)
            if first_tick is None:
                first_tick = tick
            else:
                if (tick.time - first_tick.time).total_seconds() >= seconds:
                    break



    def run(self):
        input = yield
        input = cast(Utterance, input)
        workout_name = input.get_field()
        workout = Query.en(self.workouts).where(lambda z: z.name == workout_name).to_list()
        if len(workout) != 1:
            yield WorkoutReplies.workout_not_found()
            return
        if self.music is not None:
            self.music.play()
        yield from self._wait(0)
        yield WorkoutReplies.starting(workout_name)
        rest_after_previous = None
        for item in workout[0].items:
            if rest_after_previous is not None:
                yield WorkoutReplies.rest(timedelta(seconds=rest_after_previous))
                yield from self._wait(rest_after_previous)
            yield WorkoutReplies.exercise(EXERCISE.assign(item.name), DURATION.assign(timedelta(seconds=item.duration_in_seconds)))
            first_call = item.duration_in_seconds//2
            second_call = (item.duration_in_seconds - first_call) - self.last_announcement_skip
            yield from self._wait(first_call)
            yield WorkoutReplies.keep_going()
            yield from self._wait(second_call)
            yield WorkoutReplies.almost_there()
            yield from self._wait(self.last_announcement_skip)
            rest_after_previous = item.rest_afterwards_in_seconds

        yield WorkoutReplies.done()
        if self.music is not None:
            self.music.stop()











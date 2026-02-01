from kaia.skills.workout_skill import WorkoutSkill, WorkoutIntents, Workout, WorkoutReplies, Excercise
from unittest import TestCase
from eaglesong import Scenario, Automaton, Return
from avatar.utils import TestTimeFactory
from datetime import timedelta

def S():
    workout = Workout(
        "test",
        [
            Excercise("1", 100, 5),
            Excercise("2", 200, 5)
        ]
    )

    skill = WorkoutSkill([workout], None)

    return Scenario(lambda: Automaton(skill.run, None))


class TestWorkoutSkill(TestCase):
    def test_workout_skill(self):
        factory = TestTimeFactory()
        (
            S()
            .send(WorkoutIntents.start("test"))
            .send(factory.event())
            .send(factory.shift(1).event())
            .check(
                WorkoutReplies.starting('test'),
                WorkoutReplies.exercise(exercise='1', duration=timedelta(seconds=100)),
            )

            .send(factory.shift(0).event())
            .send(factory.shift(49).event())
            .check()
            .send(factory.shift(1).event())
            .check(WorkoutReplies.keep_going())

            .send(factory.shift(0).event())
            .send(factory.shift(39).event())
            .check()
            .send(factory.shift(1).event())
            .check(WorkoutReplies.almost_there())

            .send(factory.shift(0).event())
            .send(factory.shift(9).event())
            .check()
            .send(factory.shift(1).event())
            .check(WorkoutReplies.rest(timedelta(seconds=5)))

            .send(factory.shift(0).event())
            .send(factory.shift(5).event())
            .check(
                WorkoutReplies.exercise(exercise='2', duration=timedelta(seconds=200)),
            )

            .send(factory.shift(0).event())
            .send(factory.shift(100).event())
            .check(WorkoutReplies.keep_going())

            .send(factory.shift(0).event())
            .send(factory.shift(90).event())
            .check(WorkoutReplies.almost_there())

            .send(factory.shift(0).event())
            .send(factory.shift(10).event())
            .check(WorkoutReplies.done(), Return)


            .validate()
        )




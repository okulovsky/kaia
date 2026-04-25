from brainbox.framework.container import BrainBoxRunner, BrainBoxRunnerPlaner, BrainBoxImageBuilder
from kaia.containerization import get_deployment, get_remote_working_directory

if __name__ == '__main__':
    remote_working_directory = get_remote_working_directory()
    deployment = get_deployment(
        'brainbox',
        BrainBoxImageBuilder(),
        BrainBoxRunner(
            remote_working_directory / 'brainbox',
            8090,
            True,
            planer=BrainBoxRunnerPlaner.always_on_start_only
        )
    )

    deployment.build().push().stop().remove().pull().run()


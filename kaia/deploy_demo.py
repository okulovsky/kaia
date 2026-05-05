from kaia.containerization import get_deployment, get_remote_working_directory, KaiaRunner, KaiaImageBuilder

if __name__ == '__main__':
    remote_working_directory = get_remote_working_directory()

    deployment = get_deployment(
        "kaia-demo",
        KaiaImageBuilder(),
        KaiaRunner(
            remote_working_directory,
            13000,
            True,
            debug=True
        ),
    )
    deployment.build().push().stop().remove().pull().run()


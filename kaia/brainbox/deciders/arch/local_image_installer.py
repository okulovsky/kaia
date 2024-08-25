from .docker_installer import DockerInstaller, DockerService
from kaia.brainbox.deployment import SmallImageBuilder, LocalImageSource
from pathlib import Path

class LocalImageInstaller(DockerInstaller):
    def __init__(self,
                 name: str,
                 path_to_container_code: Path,
                 dockerfile_template: str,
                 dependency_listing: None|str,
                 main_service: DockerService
                 ):

        if isinstance(dependency_listing, str):
            dependencies = [c.strip() for c in dependency_listing.split('\n') if c.strip()!='']
        else:
            dependencies = dependency_listing

        builder = SmallImageBuilder(
            path_to_container_code,
            dockerfile_template,
            dependencies,
        )

        source = LocalImageSource(name)
        super().__init__(source, main_service, builder)

    

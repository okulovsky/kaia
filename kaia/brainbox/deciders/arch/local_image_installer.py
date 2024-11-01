from .docker_installer import DockerInstaller, DockerService
from kaia.brainbox.deployment import SmallImageBuilder, LocalImageSource
from pathlib import Path

class LocalImageInstaller(DockerInstaller):
    def __init__(self,
                 name: str,
                 path_to_container_code: Path,
                 dockerfile_template: str,
                 dependency_listing: None|str,
                 main_service: DockerService,
                 custom_dependencies: None|list[list[str]] = None
                 ):
        if dependency_listing is not None:
            if not isinstance(dependency_listing, str):
                raise ValueError("Legacy issue. Use custom_dependencies instead")
            if custom_dependencies is not None:
                raise ValueError("Specify either dependency_listing or custom dependencies")
            custom_dependencies = [[c.strip() for c in dependency_listing.split('\n') if c.strip()!='']]


        builder = SmallImageBuilder(
            path_to_container_code,
            dockerfile_template,
            custom_dependencies,
        )

        source = LocalImageSource(name)
        super().__init__(source, main_service, builder)

    

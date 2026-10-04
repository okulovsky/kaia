from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ParlerTtsSettings, ParlerTtsModels
from .controller import ParlerTtsController
from .app.interface import IParlerTts


class ParlerTtsApi(
    DockerMarshallingApi[ParlerTtsSettings, ParlerTtsController],
    IParlerTts,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class ParlerTtsTaskBuilder(
    TaskBuilder,
    IParlerTts,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    pass


class ParlerTtsEntryPoint(EntryPoint[ParlerTtsTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ParlerTtsApi
        self.Settings = ParlerTtsSettings
        self.Controller = ParlerTtsController

    Models = ParlerTtsModels

    class Speakers:
        """Speaker names the v1 checkpoints were trained to reproduce consistently."""
        All = (
            'Laura', 'Gary', 'Jon', 'Lea', 'Karen', 'Rick', 'Brenda', 'David', 'Eileen',
            'Jordan', 'Mike', 'Yann', 'Joy', 'James', 'Eric', 'Lauren', 'Rose', 'Will',
            'Jason', 'Aaron', 'Naomie', 'Alisa', 'Patrick', 'Jerry', 'Tina', 'Jenna',
            'Bill', 'Tom', 'Carol', 'Barbara', 'Rebecca', 'Anna', 'Bruce', 'Emily',
        )

        @staticmethod
        def description(name: str, additional: str = 'monotone yet slightly fast in delivery') -> str:
            return (
                f"{name}'s voice is {additional}, with a very close recording "
                f"that almost has no background noise."
            )


ParlerTts = ParlerTtsEntryPoint()

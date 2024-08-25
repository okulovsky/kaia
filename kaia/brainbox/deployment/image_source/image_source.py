from ..executor import IExecutor, Command
from abc import ABC,abstractmethod

class IImageSource(ABC):
    @abstractmethod
    def get_image_name(self):
        pass

    @abstractmethod
    def pull(self, executor: IExecutor):
        pass

    @abstractmethod
    def push(self, executor: IExecutor):
        pass

    @staticmethod
    def image_name_to_container_name(image_name: str):
        image_name = image_name.split('/')[-1]
        image_name = image_name.split(':')[0]
        return  image_name

    def get_container_name(self):
        return IImageSource.image_name_to_container_name(self.get_image_name())


    def get_relevant_containers(self, executor: IExecutor) -> tuple[str,...]:
        reply = executor.execute(['docker', 'ps', '-q', '-a', '--filter', f'ancestor={self.get_image_name()}'], Command.Options(return_output=True))
        containers = [z.strip() for z in reply.decode('utf-8').strip().split('\n') if z.strip()!='']
        return tuple(containers)

    def get_relevant_images(self, executor: IExecutor) -> tuple[str,...]:
        reply = executor.execute(['docker','images',self.get_image_name(),'-q'], Command.Options(return_output=True))
        images = [z.strip() for z in reply.decode('utf-8').strip().split('\n') if z.strip() != '']
        return tuple(images)


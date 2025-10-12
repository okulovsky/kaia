from .build_context import BuildContext
from .builder_part import IBuilderPart

class User(IBuilderPart):
    def to_commands(self, context: BuildContext) -> list[str]:
        user_id = context.executor.get_machine().user_id

        result = []
        result.append(f'RUN useradd -ms /bin/bash app -u {user_id} && usermod -aG sudo app')
        result.append('USER app')
        return result

from dataclasses import dataclass
from .build_context import BuildContext


@dataclass
class Repository:
    url: str
    commit: str | None = None
    options: str = ""
    path_to_package: str = "."
    pip_install_options: str = "-e"
    install: bool = True
    remove_files: tuple[str, ...] | None = None
    remove_repo: bool = False
    recursive_clone: bool = False

    def to_commands(self, context: BuildContext) -> list[str]:
        result = []

        line_init = []
        if self.recursive_clone:
            recursive = '--recursive'
        else:
            recursive = ''
        line_init.append(f"RUN git clone {recursive} {self.url} /home/app/repo")
        line_init.append(" && cd /home/app/repo")
        if self.commit is not None:
            line_init.append(f" && git reset --hard {self.commit}")
        line_init.append(" && rm -rf .git")

        result.append("".join(line_init))

        if context.repo_fix_folder.is_dir():
            result.append(f"COPY {context.repo_fix_folder.name}/ /home/app/repo/")

        if self.remove_files is not None:
            line_remove = ["RUN "]
            for index, file in enumerate(self.remove_files):
                if index > 0:
                    line_remove.append(" && ")
                line_remove.append("rm /home/app/repo/" + file)
            result.append("".join(line_remove))

        if self.install:
            line_install = []
            line_install.append(
                f"RUN cd /home/app/repo && pip install --user {self.pip_install_options} {self.path_to_package}{self.options}"
            )
            line_install.append(" && rm -rf ~/.cache/pip")
            result.append("".join(line_install))

        if self.remove_repo:
            result.append("RUN rm -rf /home/app/repo")

        return result

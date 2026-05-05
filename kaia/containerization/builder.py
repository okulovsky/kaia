from brainbox.framework.deployment import RepoImageBuilder, SmallImageBuilder

DEFAULT_FOLDERS = (
    'foundation_kaia',
    'brainbox',
    'grammatron',
    'eaglesong',
    'avatar',
    'chara',
    'kaia',
    'talents',
)

class KaiaImageBuilder(RepoImageBuilder):
    def __init__(self):
        super().__init__(
            TEMPLATE,
            (
                'foundation_kaia',
                'brainbox',
                'grammatron',
                'eaglesong',
                'avatar',
                'chara',
                'kaia',
                'talents',
            ),
            'kaia-demo',
            (
                '**/__pycache__/',
                '**/*.pyc',
                '**/*.pyo',
                'avatar/web/frontend/',
                'avatar/web/node_modules/'
            )
        )

TEMPLATE = f'''
FROM python:3.11

RUN apt-get update \
    && apt-get install -y curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY --chown=app:app . /home/app

WORKDIR /home/app

RUN pip install  --no-cache-dir --no-compile --user -e .

ENTRYPOINT ["python", "-m", "kaia.containerization.main"]

'''
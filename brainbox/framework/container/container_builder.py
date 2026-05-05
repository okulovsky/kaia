from brainbox.framework.deployment import RepoImageBuilder, SmallImageBuilder

class BrainBoxImageBuilder(RepoImageBuilder):
    def __init__(self):
        super().__init__(
            TEMPLATE,
            ('foundation_kaia', 'brainbox'),
            'brainbox',
        )



DOCKER_INSTALL = '''
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       gnupg \
       lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*
'''


TEMPLATE = f'''
FROM python:3.11.11

{DOCKER_INSTALL}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

WORKDIR /home/app

COPY --chown=app:app . /home/app

RUN pip install --user -e .

ENTRYPOINT ["python", "-m", "brainbox.run"]
'''

FROM python:3.11

RUN apt update

RUN apt install -y wget xvfb unzip

ENV POETRY_VERSION=1.7.1
RUN pip3 install poetry==$POETRY_VERSION

WORKDIR /var/project

COPY ./pyproject.toml ./
COPY ./poetry.lock ./


RUN poetry config virtualenvs.create false

RUN poetry install --no-interaction --no-ansi --no-root

COPY ./ ./

# без этого шага admin-cli будет недоступен
RUN poetry install --only-root --no-interaction --no-ansi

ENV PYTHONPATH = ${PYTHONPATH}:/var/project:/var/project/app
WORKDIR /var/project/app


RUN echo "uvicorn --proxy-headers --forwarded-allow-ips='*' --host 0.0.0.0 --port 8000 main:app" > /run_module.sh

ENTRYPOINT ["/bin/bash", "/run_module.sh"]


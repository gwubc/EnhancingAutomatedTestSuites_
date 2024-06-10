FROM python:3.10-slim

ARG TARGET_PROGRAM_ROOT
ARG PROJECT_ROOT=/usr/src/project # The directory containing __main__ or __version__ file

ENV PROJECT_ROOT=$PROJECT_ROOT

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYNGUIN_DANGER_AWARE 1
ENV PYTHONHASHSEED 0

RUN apt update && apt install -y git
RUN pip install git+https://github.com/garyforschool/mutmut.git

WORKDIR /usr/src/scripts
COPY ./eats/docker_scripts .
RUN pip install --no-cache-dir -r ./requirements.txt

WORKDIR /usr/src/scripts_fuzzer
COPY ./eats/docker_scripts_fuzzer .

WORKDIR /usr/src/project
COPY $TARGET_PROGRAM_ROOT .
RUN if [ -f setup.cfg ]; then \
    echo "Found setup.cfg"; \
    pip install --no-cache-dir . ; \
elif [ -f requirements.txt ]; then \
    echo "Found requirements.txt"; \
    pip install --no-cache-dir -r requirements.txt ; \
else \
    echo "No dependency found."; \
fi

RUN chmod -R a-w /usr

WORKDIR /workplace

CMD ["bash"]

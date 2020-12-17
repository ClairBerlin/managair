FROM python:slim-buster
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install apt-utils netcat gettext

# Docker defaults to sh, but the 'source' command is only available in bash.
SHELL ["/bin/bash", "-c"]
RUN mkdir /code

WORKDIR /code
# install dependencies
COPY ./requirements.txt .
RUN pip3 install --upgrade pip && pip3 install wheel \
    && pip3 install --no-cache-dir -r requirements.txt

# copy application and support scripts
COPY ./managair_server /code/managair_server
COPY ./core /code/core
COPY ./accounts /code/accounts
COPY ./ingest /code/ingest
COPY schema.yaml .
COPY ./manage.py .
COPY ./entrypoint.sh .

ENV SWAGGER_JSON=./schema.yaml

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

FROM python:slim-buster
RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install apt-utils netcat

RUN mkdir /code
WORKDIR /code
# install dependencies
COPY ./requirements.txt .
RUN pip3 install --upgrade pip && pip3 install wheel \
    && pip3 install -r requirements.txt

# copy application and support scripts
COPY ./managair_server /code/managair_server
COPY ./device_manager /code/device_manager
COPY ./device_manager /code/user_manager
COPY ./device_manager /code/ts_manager
COPY ./manage.py .
COPY ./entrypoint.sh .

# run entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
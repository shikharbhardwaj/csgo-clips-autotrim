FROM python:3.8

ENV RUNTIME_PACKAGES="ffmpeg"
ENV BUILD_PACKAGES="build-essential git"

RUN apt-get update -y && \
    apt-get install -y $BUILD_PACKAGES $RUNTIME_PACKAGES && \
    apt-get autoremove -y

COPY requirements.txt /tmp/

RUN pip install --user -r /tmp/requirements.txt

RUN apt-get remove --purge -y $BUILD_PACKAGES && \
    apt-get autoremove -y

ADD . /app
WORKDIR /app

USER 9999

CMD ["/bin/bash"]

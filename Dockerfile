FROM python:3.10

ARG USERNAME=autotrim
ARG USER_UID=3000
ARG USER_GID=$USER_UID

RUN mkdir /home/$USERNAME

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -d /home/$USERNAME -m $USERNAME \
    && chown -R $USER_UID:$USER_GID /home/$USERNAME

ENV RUNTIME_PACKAGES="ffmpeg ncdu"
ENV BUILD_PACKAGES="build-essential git"

RUN apt-get update -y && \
    apt-get install -y $BUILD_PACKAGES $RUNTIME_PACKAGES && \
    apt-get autoremove -y

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

RUN apt-get remove --purge -y $BUILD_PACKAGES && \
    apt-get autoremove -y

ADD . /app
WORKDIR /app
RUN mkdir -p /app/data

RUN pip install -U openmim
RUN mim install mmcv==2.0.1 mmdet==3.1.0 mmyolo==0.6.0

RUN pip install -e .

RUN chown -R $USERNAME:$USERNAME /app

USER $USER_UID

WORKDIR /app/nbs

CMD ["bash", "../scripts/entrypoint.sh"]

FROM nvidia/cuda:11.6.0-devel-ubuntu20.04 

ENV RUNTIME_PACKAGES="gosu"
ENV BUILD_PACKAGES="build-essential git zlib1g"

RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
RUN apt-get install -y $BUILD_PACKAGES $RUNTIME_PACKAGES && \
    apt-get remove -y

# Install CUDNN
# The CUDNN deb archive needs to be downloaded and placed in the .local dir

ADD ./.local /build-local

WORKDIR /build-local

RUN dpkg -i cudnn.deb && \
    apt-key add /var/cudnn-local-repo-*/7fa2af80.pub

RUN apt-get update && \
    apt-get install -y libcudnn8-dev

# 

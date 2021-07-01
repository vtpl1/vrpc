FROM ubuntu:20.04
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y locales
RUN DEBIAN_FRONTEND=noninteractive apt install -y subversion git curl wget ninja-build build-essential gdb python3-tk python3-pip python3-dev

RUN pip3 install -U pip
COPY requirements.dev.txt /tmp/pip-tmp/
RUN pip install --no-cache-dir -r /tmp/pip-tmp/requirements.dev.txt \
    && rm -rf /tmp/pip-tmp

RUN ln -s /usr/bin/python3 /usr/bin/python

# RUN pip install protobuf

RUN wget https://github.com/protocolbuffers/protobuf/releases/download/v3.17.3/protobuf-all-3.17.3.tar.gz && \
    tar -xzf protobuf-all-3.17.3.tar.gz && cd protobuf-3.17.3/ && ./configure --prefix=/usr && make && make install && \
    cd .. && rm protobuf-all-3.17.3.tar.gz && rm -rf protobuf-3.17.3

RUN pip install "betterproto[compiler]"
RUN pip install ruamel.yaml
RUN pip install opencv-python numpy
RUN DEBIAN_FRONTEND=noninteractive apt install -y ffmpeg libsm6 libxext6
#RUN pip install grpcio-tools

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN groupmod --gid $USER_GID $USERNAME \
    && usermod --uid $USER_UID --gid $USER_GID $USERNAME \
    && chown -R $USER_UID:$USER_GID /home/$USERNAME
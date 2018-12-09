FROM debian:9-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt update && \
    apt install -y git python3 python3-pip python3-setuptools python3-six && \
    \
    pip3 install cryptography==2.4.2 && \
    pip3 install "idna<2.8,>=2.5" && \
    pip3 install git+https://github.com/aayars/comrade && \
    post-media --help && \
    \
    apt remove -y git python3-pip && \
    apt autoremove -y

CMD post-media --help

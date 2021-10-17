FROM ubuntu:18.04
 
RUN apt update && apt install -y \
  cmake \
  ffmpeg \
  python3-dev \
  python3-pip \
  libpq-dev \
  libssl-dev \
  bmon \
  slurm \
  tcptrack \
  iftop \
  iptraf-ng \
  net-tools

RUN pip3 install azure-cognitiveservices-speech flask celery[redis] psycopg2

ENV C_FORCE_ROOT true

COPY ./ /app/
WORKDIR /app/




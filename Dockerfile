FROM ubuntu:18.04
 
RUN apt update && apt install -y \
  cmake \
  ffmpeg \
  python3-dev \
  python3-pip \
  libpq-dev \
  libssl-dev \
  iptraf-ng \
  net-tools \
  supervisor

RUN pip3 install azure-cognitiveservices-speech flask celery[redis] psycopg2

ENV C_FORCE_ROOT true

COPY ./app/ /app/
WORKDIR /app/

# COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./run.sh /app/run.sh

# ENTRYPOINT ["/usr/bin/supervisord"]


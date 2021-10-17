FROM ubuntu:18.04

RUN apt update && apt install -y cmake ffmpeg python3-dev python3-pip
RUN pip3 install azure-cognitiveservices-speech python-telegram-bot

COPY ./ /app/
WORKDIR /app/
RUN rm *key auth.json



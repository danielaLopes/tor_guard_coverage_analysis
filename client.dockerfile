FROM ubuntu:20.04

WORKDIR /app

RUN apt-get update --fix-missing
RUN apt-get install -y software-properties-common
RUN apt-get install -y python3-pip
RUN apt install -y tor
#syntax=docker/dockerfile:1

FROM python:3.10-slim-bullseye

ENV TZ="America/Chicago"
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app
RUN mkdir --parents /app/data/receipts
RUN apt update
RUN apt install fonts-liberation2 -y
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY src src

CMD [ "python3", "src/main.py"]

#syntax=docker/dockerfile:1

FROM python:3.10-slim-bullseye

ENV TZ="America/Chicago"
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY src src

CMD [ "python3", "src/main.py"]

# syntax=docker/dockerfile:1

FROM ubuntu:20.04

WORKDIR /app
RUN apt-get update && apt-get install -y \
  python3-pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY bot.py .
COPY quotes.txt .

CMD [ "python3", "bot.py"]
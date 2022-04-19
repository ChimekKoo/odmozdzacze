FROM ubuntu:latest

RUN apt-get update -y && apt-get install -y python3-pip

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

CMD [ "python3", "app/wsgi.py" ]
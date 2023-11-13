FROM python:3.11.2-alpine

LABEL org.opencontainers.image.source="https://github.com/ChimekKoo/odmozdzacze"

COPY . /app
WORKDIR /app

RUN apk add --no-cache gcc libc-dev linux-headers build-base
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["uwsgi", "--ini", "uwsgi.ini"]

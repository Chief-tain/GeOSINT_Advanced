FROM python:3.11-slim-buster as parser
COPY parser/requirements.txt /app/parser/requirements.txt
COPY shared/requirements.txt /app/shared/requirements.txt

RUN pip install -r /app/parser/requirements.txt

RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader stopwords

FROM parser

COPY ../parser /app/parser
COPY ../shared /app/shared

WORKDIR /app/parser
ENV PYTHONPATH "${PYTHONPATH}:/app"
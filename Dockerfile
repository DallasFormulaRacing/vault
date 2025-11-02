# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN pip install --no-cache-dir pipenv

WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pipenv install

COPY src /app/src
COPY utils /app/utils

EXPOSE 8080

CMD ["pipenv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
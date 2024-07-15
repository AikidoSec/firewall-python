# Use an official Python runtime as a parent image
FROM python:3

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY ./sample-apps/flask-mysql/Pipfile ./
RUN pip install --no-cache-dir pipenv && pipenv install

# Copy the project code into the container
COPY sample-apps/flask-mysql ./
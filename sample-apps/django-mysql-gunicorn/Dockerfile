# Use an official Python runtime as a parent image
FROM python:3

#Copy code base
COPY ./ /tmp

# Set the working directory
WORKDIR /app

# Install dependencies
RUN mv /tmp/sample-apps/django-mysql-gunicorn/requirements.txt ./
RUN pip install -r requirements.txt

# Build and install aikido_firewall from source
WORKDIR /tmp
RUN pip install poetry
RUN make build
RUN pip install ./dist/aikido_firewall-0.1.0.tar.gz
RUN pip list

WORKDIR /app

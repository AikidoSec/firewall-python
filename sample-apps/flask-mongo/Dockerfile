# Use an official Python runtime as a parent image
FROM python:3

#Copy code base
COPY ./ /tmp

# Set the working directory
WORKDIR /app

# Install dependencies
RUN mv /tmp/sample-apps/flask-mongo/requirements.txt ./
RUN pip install -r requirements.txt

# Build and install aikido_firewall from source
WORKDIR /tmp
RUN pip install poetry
RUN rm -r ./dist
RUN make build
RUN mv ./dist/aikido_firewall-*.tar.gz ./dist/aikido_firewall.tar.gz
RUN pip install ./dist/aikido_firewall.tar.gz
RUN pip list

WORKDIR /app

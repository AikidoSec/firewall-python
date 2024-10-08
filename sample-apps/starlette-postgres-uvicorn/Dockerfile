# Use an official Python runtime as a parent image
FROM python:3

#Copy code base
COPY ./ /tmp

# Set the working directory
WORKDIR /app

# Install dependencies
RUN mv /tmp/sample-apps/starlette-postgres-uvicorn/requirements.txt ./
RUN pip install -r requirements.txt

# Build and install aikido_zen from source
WORKDIR /tmp
RUN pip install poetry
RUN rm -rf ./dist
RUN make build
RUN mv ./dist/aikido_zen-*.tar.gz ./dist/aikido_zen.tar.gz
RUN pip install ./dist/aikido_zen.tar.gz
RUN pip list

WORKDIR /app

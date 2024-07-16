# Use an official Python runtime as a parent image
FROM python:3

#Copy code base
COPY ./ /tmp

# Set the working directory
WORKDIR /app

# Install dependencies
RUN mv /tmp/sample-apps/django-mysql/requirements.txt ./
RUN pip install -r requirements.txt

# Install aikido_firewall from source
#RUN pip install /tmp
RUN pip list
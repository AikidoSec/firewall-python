# Use an official Python runtime as a parent image
FROM python:3

#Copy code base
COPY ./ /app

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "mock_aikido_core.py", "5000"]

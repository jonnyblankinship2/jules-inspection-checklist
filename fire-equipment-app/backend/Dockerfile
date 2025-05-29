# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by psycopg2 or other libraries
# RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/* 
# Above line can be uncommented if psycopg2-binary fails and full psycopg2 is needed.
# For psycopg2-binary, typically system deps are less of an issue.

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Make port 8000 available to the world outside this container
# (Gunicorn will run on this port, or Flask dev server if used)
EXPOSE 8000

# Define command to run the app using Gunicorn (recommended for production)
# Ensure gunicorn is in requirements.txt if you use this
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"] 
   
# For simplicity in environments without Gunicorn setup, use Flask's dev server.
# NOTE: Flask's built-in server is not recommended for production.
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]

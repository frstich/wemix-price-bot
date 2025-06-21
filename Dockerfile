# Dockerfile

# 1. Use an official Python runtime as a parent image.
# Using 'slim' is a good practice for smaller image sizes.
FROM python:3.13-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file into the container
# This is done first to leverage Docker's build cache.
# If requirements.txt doesn't change, this layer won't be rebuilt, speeding up future builds.
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application's code into the container
COPY . .

# 6. Specify the command to run when the container starts
# This will execute your bot script.
CMD ["python", "-u", "bot.py"]
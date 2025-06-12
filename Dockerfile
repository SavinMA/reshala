# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container at /app
COPY src/ /app/src/

# Expose the port the app runs on. (If using webhooks, uncomment this line)
# EXPOSE 8080

# Run bot.py when the container launches
CMD ["python", "src/bot.py"] 
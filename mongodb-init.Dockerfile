FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir pymongo python-dotenv

# Copy the initialization script and .env file
COPY mongo_init.py .env* ./

# Make the script executable
RUN chmod +x mongo_init.py

# Set the script as the entrypoint
CMD ["python", "mongo_init.py"]

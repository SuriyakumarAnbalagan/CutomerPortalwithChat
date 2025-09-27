# Use Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# Match filename in this repo: requirement.txt
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 8080

# Start Flask app with Gunicorn (Cloud Run expects :8080)
CMD ["gunicorn", "-b", ":8080", "app:app"]

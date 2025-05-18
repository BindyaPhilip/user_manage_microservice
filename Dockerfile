# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (User Management runs on 8002)
EXPOSE 8002

# Run the Django app
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "user_management.wsgi:application"]
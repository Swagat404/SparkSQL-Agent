FROM python:3.9-slim

# Install Java and system dependencies
RUN apt-get update && apt-get install -y \
    default-jdk \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$PATH:$JAVA_HOME/bin

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install 'uvicorn[standard]' websockets

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Start the backend service
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"] 
#!/bin/bash

set -e  # Exit on error

echo "Stopping existing containers..."
docker-compose down

echo "Building backend container with WebSocket support..."
docker-compose build backend

echo "Starting services..."
docker-compose up -d

echo "==============================="
echo "Services started successfully!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3001"
echo "==============================="
echo "WebSocket endpoint: ws://localhost:8000/ws/phases/{session_id}"
echo "To check logs: docker-compose logs -f backend" 
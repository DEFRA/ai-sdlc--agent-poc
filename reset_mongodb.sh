#!/bin/bash
# Reset and reinitialize MongoDB

echo "Stopping MongoDB containers..."
docker-compose down

echo "Removing MongoDB volume..."
docker volume rm ai-sdlc--agent-poc_mongodb_data || echo "Volume not found or already removed."

echo "Starting MongoDB container..."
docker-compose up -d mongodb

echo "Waiting for MongoDB to start (15 seconds)..."
sleep 15

echo "Running MongoDB initialization script..."
python mongo_init.py

echo "Verifying MongoDB connection..."
python verify_mongodb.py

echo "MongoDB reset and initialization completed."

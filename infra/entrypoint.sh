#!/bin/sh

echo "Waiting for database to be ready..."
until alembic -c src/alembic.ini current > /dev/null 2>&1; do
    echo "Database not ready yet, retrying in 2 seconds..."
    sleep 2
done

echo "Applying migrations..."
alembic -c src/alembic.ini upgrade head

if [ $? -ne 0 ]; then
    echo "Migrations failed! Exiting."
    exit 1
fi

echo "Starting server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000

#!/bin/bash
# Run Celery worker for background tasks
# Usage: ./scripts/run_celery_worker.sh

cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Celery worker..."
celery -A celery_app.celery worker --loglevel=info --queues=notifications

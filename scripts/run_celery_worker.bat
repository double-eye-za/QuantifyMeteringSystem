@echo off
REM Run Celery worker for background tasks
REM Usage: run_celery_worker.bat

cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting Celery worker...
celery -A celery_app.celery worker --loglevel=info --queues=notifications --pool=solo

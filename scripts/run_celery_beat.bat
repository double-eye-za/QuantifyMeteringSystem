@echo off
REM Run Celery beat scheduler for periodic tasks
REM Usage: run_celery_beat.bat

cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting Celery beat scheduler...
celery -A celery_app.celery beat --loglevel=info

# Placeholder Dockerfile for the FastAPI backend service.
# See TASKS.md T51.
#
# TODO:
# - multi-stage build with the dependency-install layer cached separately
#   from application code
# - non-root user
# - CMD to launch uvicorn once app.main:app is fully implemented

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

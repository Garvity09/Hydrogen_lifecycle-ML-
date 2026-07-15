FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY run.py .
COPY src/ ./src/
COPY static/ ./static/

# Expose FastAPI port
EXPOSE 8000

# Run orchestrator and launch uvicorn
CMD ["python", "run.py"]

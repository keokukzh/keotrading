FROM python:3.11-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application
COPY src /code/src
COPY data /code/data
COPY configs /code/configs

# Environment variables
ENV PYTHONPATH=/code
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run with gunicorn for production
# Workers: 1 per CPU core
# Using uvicorn worker for async support
CMD ["python", "-m", "uvicorn", "src.dashboard.api:app", "--host", "0.0.0.0", "--port", "8000"]

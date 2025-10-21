FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr (good for Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app



# Install python deps
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port used by uvicorn
EXPOSE 8000



# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
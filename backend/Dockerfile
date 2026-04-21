FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Tesseract for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install CPU-only torch first to avoid pulling ~3GB of NVIDIA CUDA wheels
# that the default torch 2.x pulls in on Linux. sentence-transformers works
# fine on CPU-only torch for this project's scale.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.2.2

# Install remaining Python dependencies (pip will see torch is already satisfied)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with hot reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

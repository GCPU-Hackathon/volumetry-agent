FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade google-genai

COPY . .

# Create storage directory
RUN mkdir -p /app/storage/studies

EXPOSE 8000
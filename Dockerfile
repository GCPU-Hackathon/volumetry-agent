FROM python:3.10

# Accept build arguments for user/group IDs
ARG WWWUSER=1000
ARG WWWGROUP=1000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade google-genai

# Create user and group with specified IDs
RUN groupadd -g ${WWWGROUP} appgroup || true && \
    useradd -m -u ${WWWUSER} -g ${WWWGROUP} -s /bin/bash appuser || true

COPY . .

# Change ownership of copied files
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser
ENV HOME=/home/appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
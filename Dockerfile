FROM python:3.12-alpine3.23

WORKDIR /app

# Run apk add update && install -y --no-install-recommends
RUN apk add --no-cache \
    build-base

# Copy requirement and install library & packages \
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8000", "fully_automated_jira_github:app"]
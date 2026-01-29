FROM python:3.12-alpine3.23

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement and install library & packages \
COPY requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt

COPY Jira-github_automation .

EXPOSE 8080

CMD ["guicorn", "-w", "4", "--bind", "0.0.0.0:8080", "fully_automated_jira_github:app"]
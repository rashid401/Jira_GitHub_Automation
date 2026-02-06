FROM python:3.12-alpine3.23

WORKDIR /app

#RUN apk add update && apt-get install -y --no-install-recommends \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/*

# Run apk add update && install -y --no-install-recommends
RUN apk add --no-cahce \
    build-base

# Copy requirement and install library & packages \
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY Jira-github_automation .

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8000", "fully_automated_jira_github:app"]
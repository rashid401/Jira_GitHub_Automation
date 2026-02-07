import hmac
import hashlib
import requests
import logging
import redis

from flask import Flask, request, abort
from jira import JIRA
from logging.handlers import RotatingFileHandler
from datetime import timedelta, datetime
from app.config import Config

# Load and validate configuration
Config.datavalidate()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github_jira_automation")

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(messages)s')

# File handler
file_handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream handler (for docker console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Initialize Redis
cache = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout = 5,
    retry_on_timeout=True
)

app = Flask(__name__)

due_date = datetime.now() + timedelta(days=7)

jira_client = JIRA(server=Config.JIRA_SERVER, basic_auth=(Config.JIRA_USER, Config.JIRA_API_TOKEN))


def verify_signature(payload_body, header_signature):
    #Verify that the payload was sent from valid GitHub by validating the HMAC signature.
    if not header_signature:
        return False

    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha256':
        return False

    hash_object = hmac.new(Config.GITHUB_SECRET.encode('utf-8'),
                           msg=payload_body,
                           digestmod=hashlib.sha256
                           )
    return hmac.compare_digest(hash_object.hexdigest(), signature)


def post_github_comment(issue_url, message):
    #Posts a comment back to the GitHub Issue.
    url = f"{issue_url}/comments"
    header = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": message}
    response = requests.post(url, json=data, headers=header)
    return response.status_code


@app.route('/create_jira', methods=['POST'])
def create_jira():
    logger.info("Received a webhook request from GitHub")

    # Catch the unique delivery id of GitHub Webhook Event
    delivery_id = request.headers.get('X-gitHub-Delivery')

    if delivery_id:
        try:
            if cache.exists(delivery_id):
                logger.warning(f"Duplicate webhook detected: {delivery_id}. Skipping....")
                return {"status": "ignored", "reason": "duplicate request"}, 200

            # Record the delivery id to avoid again processing the same webhook delivery
            cache.setex(delivery_id, Config.ONE_DAY, "processed")

        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            # If Redis is down, process without deduplication.
            logger.error("Redis is down! Processing without deduplication.")
        except Exception as e:
            # Log the error incase redis checked fail
            logger.error(f"Redis check failed: {str(e)}")

    try:
        signature = request.headers.get('X-Hub-Signature-256')
        if not verify_signature(request.data, signature):
            abort(403, "Invalid Signature")

        payload = request.json

        # Check if this is a comment event and contains the keyword  /jira
        if 'comment' in payload and '/jira' in payload['comment'].get('body', '').lower():
            issue_title = payload['issue']['title']
            issue_url = payload['issue']['html_url']
            commenter = payload['issue']['user']['login']
            api_url = payload['issue']['url']

            issue_body = "\n".join([
                line for line in payload['issue']['body'].splitlines()
                if "/jira" not in line.casefold()
            ])

            logger.info(f"Trigger keyword found in comment by {commenter}")

            # construct Jira details
            summary = f"[Github] {issue_title}"
            description = (
                f"*Ticket created via Github comment by {commenter}*\n\n"
                f"*Original Issue Body:*\n{issue_body}\n\n"
                f"*Created from Github issue:* {issue_url}"
            )

            # Create new issue in jira
            new_issue = jira_client.create_issue(
                project=Config.JIRA_PROJECT_KEY,
                summary=summary,
                description=description,
                issuetype={'name': 'Issue'},
                duedate=due_date
            )

            # Comment jira ticket details in Github issue
            jira_link = f"{Config.JIRA_SERVER}/browse/{new_issue.key}"
            msg = f"**Jira Ticket created!**\nkey: [{new_issue.key}]({jira_link})"
            post_github_comment(api_url, msg)

            logger.info(f"Successfully created Jira issue: {new_issue.key}")
            return {"status": "success", "Jira_key": new_issue.key}, 201

        else:
            logger.info("Webhook received, but no '/jira' keyword found. Skipping......")
            return {"Status": "ignored", "reason": "no keyword"}, 200

    except Exception as e:
        logger.error(f"Failed to process webhook: {str(e)}", exc_info=True)
        return "Internal Server Error", 500


if __name__ == '__main__':
    app.run('0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
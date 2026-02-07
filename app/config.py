import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    # Environment variable
    GITHUB_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET", "enter_secret_key')
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    JIRA_SERVER = os.environ.get('JIRA_SERVER')
    JIRA_USER = os.environ.get('JIRA_USER')
    JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')
    JIRA_PROJECT_KEY = os.environ.get('JIRA_PROJECT_KEY', 'GIH')

    LOG_FILE = os.environ.get('LOG_FILE', 'logs/github_jira_automation.log')

    # Flask Settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    PORT = int(os.environ.get('PORT', 8000))
    ONE_DAY = 60 * 60 * 24


    # Redis setting
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis_service')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

    @staticmethod
    def datavalidate():
        """Ensure all required secrets are present"""
        required = [
            'GITHUB_WEBHOOK_SECRET',
            'GITHUB_TOKEN',
            'JIRA_SERVER',
            'JIRA_API_TOKEN'
        ]
        missing_env_var = [var for var in required if not os.environ.get(var)]
        if missing_env_var:
            raise EnvironmentError(f"Missing required environment variable(s): {','.join(missing_env_var)}")
import asyncio
import os
from amocrm.v2 import tokens
import redis



DEBUG = os.environ.get('DEBUG', 'TRUE') == 'TRUE'

if DEBUG:
    from dotenv import load_dotenv
    load_dotenv()

ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
INTEGRATION_ID = os.environ.get('INTEGRATION_ID')

BASE_URL = os.environ.get('BASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY')
AUTH_CODE = os.environ.get('AUTH_CODE')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
REDIS_HOST = os.environ.get('REDIS_HOS', 'localhost')

redis_client = redis.Redis(host=REDIS_HOST, port=6379)


settings = {
    "backup_file_path": "./tokens",
    "encryption_key": ENCRYPTION_KEY,
    "integration_id": INTEGRATION_ID,
    "secret_key": SECRET_KEY,
    "auth_code": AUTH_CODE,
    "base_url": BASE_URL,
    "redirect_uri": REDIRECT_URI,
}

tokens.default_token_manager(
    client_id=INTEGRATION_ID,
    client_secret=SECRET_KEY,
    subdomain='usadbavip',
    redirect_url=REDIRECT_URI,
    storage=tokens.RedisTokensStorage(redis_client),  # by default FileTokensStorage
)

tokens.default_token_manager.init(code=AUTH_CODE, skip_error=True)

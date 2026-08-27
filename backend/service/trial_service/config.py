import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

TRIAL_LIMIT = 5
TRIAL_TTL_SECONDS = 60 * 60 * 24 * 30
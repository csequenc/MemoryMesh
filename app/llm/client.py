import os
import time
import threading

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")


# Groq SDK handles retries for retryable API errors.
groq_client = Groq(
    api_key=api_key,
    max_retries=3
)


# Simple shared request-spacing limiter.
MIN_REQUEST_INTERVAL = 2.0

last_request_time = 0.0
request_lock = threading.Lock()


def create_chat_completion(**kwargs):
    global last_request_time

    with request_lock:
        elapsed = time.monotonic() - last_request_time
        remaining = MIN_REQUEST_INTERVAL - elapsed

        if remaining > 0:
            time.sleep(remaining)

        last_request_time = time.monotonic()

    return groq_client.chat.completions.create(**kwargs)
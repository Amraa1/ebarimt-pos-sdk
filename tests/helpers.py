from dotenv import load_dotenv
import pytest
import os

load_dotenv()

TOKEN_URL = os.getenv("TOKEN_URL", "https://example.com")
BASE_API_URL = os.getenv("BASE_API_URL", "https://example.com")
BASE_REST_URL = os.getenv("BASE_REST_URL", "https://example.com")
CLIENT_ID = os.getenv("CLIENT_ID", "test_client")
USERNAME = os.getenv("USERNAME", "ebarimt_tester")
PASSWORD = os.getenv("PASSWORD", "123456")

msg = "Missing env vars"

if TOKEN_URL is None:
        raise Exception(msg)
if CLIENT_ID is None:
    raise Exception(msg)
if USERNAME is None:
    raise Exception(msg)
if PASSWORD is None:
    raise Exception(msg)


pytest.skip(msg, allow_module_level=True)
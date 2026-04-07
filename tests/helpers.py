from dotenv import load_dotenv
import os

load_dotenv()

TOKEN_URL = os.getenv("TOKEN_URL", "https://example.com")
BASE_API_URL = os.getenv("BASE_API_URL", "https://example.com")
BASE_REST_URL = os.getenv("BASE_REST_URL", "https://example.com")
TIN = os.getenv("TIN", "37900846788")
CLIENT_ID = os.getenv("CLIENT_ID", "test_client")
USERNAME = os.getenv("USERNAME", "ebarimt_tester")
PASSWORD = os.getenv("PASSWORD", "123456")


print(TOKEN_URL)
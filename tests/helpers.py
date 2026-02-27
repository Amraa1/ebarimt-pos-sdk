from dotenv import load_dotenv

load_dotenv()

import os

TOKEN_URL = os.getenv("TOKEN_URL")
BASE_API_URL = os.getenv("BASE_API_URL")
BASE_REST_URL = os.getenv("BASE_REST_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

msg = "Missing env vars"

if TOKEN_URL is None:
        raise Exception(msg)
if CLIENT_ID is None:
    raise Exception(msg)
if USERNAME is None:
    raise Exception(msg)
if PASSWORD is None:
    raise Exception(msg)


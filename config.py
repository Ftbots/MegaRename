import os

# Correct way to get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Environment variable name should be used here
API_ID = os.getenv("API_ID")  # Same here
API_HASH = os.getenv("API_HASH")  # Same here

# MEGA credentials
MEGA_CREDENTIALS = {
    "email": os.getenv("MEGA_EMAIL"),
    "password": os.getenv("MEGA_PASSWORD")
}

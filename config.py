import os

# Correct way to get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# MEGA credentials
MEGA_CREDENTIALS = {
    "email": os.getenv("MEGA_EMAIL"),
    "password": os.getenv("MEGA_PASSWORD")
}

# Admin user ID
ADMIN_USER_ID = 891959176  # Your Telegram user ID

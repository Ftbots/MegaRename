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
ADMINS = [891959176, YOUR_TELEGRAM_USER_ID] # Add your user ID here

# MongoDB connection string
MONGO_URI = "mongodb+srv://suryabhai991100:pPmTrc0DoyPsEcmn@cluster0.xpua4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Force Subscribe Channel
FORCE_SUB_CHANNEL = -1002320532990 # Your private channel ID

FSUB_TXT = "<pre>Hello 👋, {first}</pre>\n\n<i>You need to join my Updates Channel to use me.</i>\n\n"

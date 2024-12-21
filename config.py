import os

# Correct way to get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "7658008644:AAGtekRQRLwbu9b-bW6mJ2-w1BZGVeHJVDE")
API_ID = os.getenv("API_ID", "24994752")
API_HASH = os.getenv("API_HASH", "1c9b10f27f4ab2811ed4f102cc005837")

# MEGA credentials
MEGA_CREDENTIALS = {
    "email": os.getenv("MEGA_EMAIL"),
    "password": os.getenv("MEGA_PASSWORD")
}

# Admin user ID
ADMIN_USER_ID = ["891959176", "7597122443"] # Add your user ID here

ADMINS = ADMIN_USER_ID

# MongoDB connection string
MONGO_URI = "mongodb+srv://suryabhai991100:pPmTrc0DoyPsEcmn@cluster0.xpua4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Force Subscribe Channel
FORCE_SUB_CHANNEL = -1002320532990 # Your private channel ID

FSUB_TXT = "<pre>Hello 👋, {first}</pre>\n\n<i>You need to join my Updates Channel to use me.</i>\n\n"

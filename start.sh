#!/bin/sh

echo "Installing/Upgrading requirements"
pip install -U -r requirements.txt

echo "Setting env vars"
# enter you own variables here

# discord bot key
export KEY_DISCORD="YOUR_KEY"
# fnbr.co api key
export KEY_FNBR="YOUR_KEY"
# fortnite tracker network api key
export KEY_TRACKERNETWORK="YOUR_KEY"
# your postgresql access url (see README for details on setting up)
export DATABASE_URL="postgresql://my.database"

echo "Starting..."
python ./bot.py

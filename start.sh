#!/bin/sh

echo "Installing/Upgrading requirements"
pip install -r requirements.txt

echo "Setting env vars"

# enter you own variables here
export KEY_DISCORD="YOUR_KEY" # discord bot key
export KEY_FNBR="YOUR_KEY" # fnbr.co api key
export KEY_TRACKERNETWORK="YOUR_KEY" # fortnite tracker network api key
export DATABASE_URL="postgresql://my.database" # your postgresql access url (see README for details on setting up)

echo "Starting..."
python ./bot.py

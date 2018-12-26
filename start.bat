
echo "Installing/Upgrading requirements"
pip install -r requirements.txt

echo "Setting env vars"

rem enter you own variables here
SET KEY_DISCORD="YOUR_KEY" rem discord bot key
SET KEY_FNBR="YOUR_KEY" rem fnbr.co api key
SET KEY_TRACKERNETWORK="YOUR_KEY" rem fortnite tracker network api key
SET DATABASE_URL="postgresql://my.database" rem your postgresql access url (see README for details on setting up)

echo "Starting..."
python ./bot.py

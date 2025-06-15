import discord
import requests
import asyncio
import os
from flask import Flask
from threading import Thread

# --- FLASK WEB SERVER (to keep Render happy) ---
app = Flask('')


@app.route('/')
def home():
    return "I am alive and the bot is running!"


def run_flask_app():
    # The host must be '0.0.0.0' to be reachable by Render
    app.run(host='0.0.0.0', port=8080)


def start_web_server():
    """Starts the Flask web server in a separate thread."""
    server_thread = Thread(target=run_flask_app)
    server_thread.start()


# --- DISCORD BOT CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID_TO_RENAME = int(os.getenv("CHANNEL_ID_TO_RENAME", 0))

COINGECKO_ID = "wemix-token"
VS_CURRENCY = "usd"
UPDATE_FREQUENCY_SECONDS = 30
NICKNAME_PREFIX = "WEMIX"
ACTIVITY_TEXT = "WEMIX at"
CHANNEL_PREFIX = "📈-wemix"
# --- END CONFIGURATION ---

# Define the necessary intents for the bot
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


def get_crypto_price(coin_id, currency):
    """Fetches the current price from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get(coin_id, {}).get(currency)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price from CoinGecko: {e}")
        return None


async def update_price_task():
    """The main loop that fetches the price and updates all Discord elements."""
    await client.wait_until_ready()

    while not client.is_closed():
        price = get_crypto_price(COINGECKO_ID, VS_CURRENCY)

        if price is not None:
            price_display = f"${price:,.4f}"
            price_channel = f"{price:.2f}".replace('.', '-')
            print(f"Updating price: {COINGECKO_ID.upper()} = {price_display}")

            try:
                # Update Activity Status
                activity = discord.Activity(
                    type=discord.ActivityType.watching, name=f"{ACTIVITY_TEXT} {price_display}")
                await client.change_presence(activity=activity)

                # Update Nickname
                for guild in client.guilds:
                    me = guild.get_member(client.user.id)
                    if me:
                        await me.edit(nick=f"{NICKNAME_PREFIX} {price_display}")

                # Update Channel Name
                channel_to_update = client.get_channel(CHANNEL_ID_TO_RENAME)
                if channel_to_update:
                    await channel_to_update.edit(name=f"{CHANNEL_PREFIX}-{price_channel}")

            except Exception as e:
                print(f"An unexpected error occurred during update: {e}")

        else:
            print("Could not retrieve price. Will try again.")

        await asyncio.sleep(UPDATE_FREQUENCY_SECONDS)


@client.event
async def on_ready():
    """Event that runs when the bot is connected."""
    print(f'Logged in as {client.user.name}')
    client.loop.create_task(update_price_task())

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not BOT_TOKEN or CHANNEL_ID_TO_RENAME == 0:
        print("!!! CONFIGURATION ERROR !!!")
        print("You must set BOT_TOKEN and CHANNEL_ID_TO_RENAME in the Render Environment Variables.")
    else:
        # Start the web server to keep Render happy
        start_web_server()

        # Start the Discord bot
        client.run(BOT_TOKEN)

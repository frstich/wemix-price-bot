import discord
import requests
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---

# 1. Your Discord Bot Token (from the Discord Developer Portal)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. The CoinGecko ID for the coin you want to track.
COINGECKO_ID = "wemix-token"

# 3. The currency to display the price in (e.g., 'usd', 'eur', 'jpy').
VS_CURRENCY = "usd"

# 4. The ID of the channel you want to rename.
#    In Discord, right-click the channel -> "Copy Channel ID".
#    (You must have Developer Mode enabled in Discord Settings -> Advanced)
CHANNEL_ID_TO_RENAME = 1382821974010626108

# 5. How often to update the price, in seconds.
#    Discord's rate limit is 5 updates per 60 seconds. 15-30 seconds is safe and effective.
UPDATE_FREQUENCY_SECONDS = 30

# 6. Customize the display text (optional)
NICKNAME_PREFIX = "WEMIX"
ACTIVITY_TEXT = "WEMIX at"
CHANNEL_PREFIX = "📈-wemix"  # No spaces or special characters except hyphens

# --- END CONFIGURATION ---


# Define the necessary intents for the bot
intents = discord.Intents.default()
intents.members = True  # Required for changing nicknames
client = discord.Client(intents=intents)


def get_crypto_price(coin_id, currency):
    """Fetches the current price of a cryptocurrency from CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        price = data.get(coin_id, {}).get(currency)
        return price
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price from CoinGecko: {e}")
        return None


async def update_price_task():
    """The main loop that fetches the price and updates all Discord elements."""
    await client.wait_until_ready()

    while not client.is_closed():
        price = get_crypto_price(COINGECKO_ID, VS_CURRENCY)

        if price is not None:
            # Format strings for different uses
            # For nickname and activity (e.g., $1.2345)
            price_display = f"${price:,.4f}"
            # Channel names cannot have dots, so we replace them with hyphens
            price_channel = f"{price:.2f}".replace(
                '.', '-')  # For channel name (e.g., 1-23)

            print(f"Updating price: {COINGECKO_ID.upper()} = {price_display}")

            try:
                # --- METHOD 1: Update Bot Activity Status ---
                activity = discord.Activity(
                    type=discord.ActivityType.watching, name=f"{ACTIVITY_TEXT} {price_display}")
                await client.change_presence(activity=activity)

                # --- METHOD 2: Update Bot Nickname in all servers ---
                for guild in client.guilds:
                    me = guild.get_member(client.user.id)
                    if me:
                        await me.edit(nick=f"{NICKNAME_PREFIX} {price_display}")

                # --- METHOD 3: Update a Channel Name ---
                channel_to_update = client.get_channel(CHANNEL_ID_TO_RENAME)
                if channel_to_update:
                    await channel_to_update.edit(name=f"{CHANNEL_PREFIX}-{price_channel}")
                else:
                    print(
                        f"Error: Could not find channel with ID {CHANNEL_ID_TO_RENAME}. Make sure the ID is correct and the bot is in the server.")

            except discord.errors.Forbidden as e:
                print(
                    f"Error: Bot lacks permissions. Make sure it has 'Change Nickname' and 'Manage Channels' permissions. Details: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during update: {e}")

        else:
            print("Could not retrieve price. Will try again.")

        await asyncio.sleep(UPDATE_FREQUENCY_SECONDS)


@client.event
async def on_ready():
    """Event that runs when the bot is connected and ready."""
    print(f'Logged in as {client.user.name} ({client.user.id})')
    print('Starting the all-in-one price update loop...')
    client.loop.create_task(update_price_task())

# Run the bot
if not BOT_TOKEN or CHANNEL_ID_TO_RENAME == 0:
    print("!!! CONFIGURATION ERROR !!!")
    print("You must set BOT_TOKEN and CHANNEL_ID_TO_RENAME in the Render Environment Variables.")
else:
    client.run(BOT_TOKEN)

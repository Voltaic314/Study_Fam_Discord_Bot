import discord
from discord.ext import commands
from discord import app_commands
import responses
import secrets


# Send messages
async def send_message(message, is_private):
    try:
        response = responses.handle_response(str(message.content))
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)


def run_discord_bot():
    TOKEN = secrets.discord_bot_credentials["API_Key"]
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):

        # Make sure bot doesn't get stuck in an infinite loop
        if message.author == client.user:
            return

        # Get data about the user
        username = str(message.author)
        user_message = str(message.content)
        channel = str(message.channel)

        # Debug printing
        print(f"{username} said: '{user_message}' ({channel})")

        await send_message(message, is_private=False)

    # Remember to run your bot with your personal TOKEN
    client.run(TOKEN)


if __name__ == "__main__":
    run_discord_bot()

import discord
from discord.ext import commands
from discord import app_commands


class Commands_For_Bot:
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @tree.command(name="commandname", description="My first application Command", guild=discord.Object(
        id=12417128931))  # Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.

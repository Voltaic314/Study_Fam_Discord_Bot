import discord
from discord import app_commands
import secrets


class Focus_Bot_Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False  # we use this so the bot doesn't sync commands more than once

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:  # check if slash commands have been synced
            await tree.sync()
            self.synced = True
        print(f"We have logged in as {self.user}.")


client = Focus_Bot_Client()
tree = app_commands.CommandTree(client)
Focus_Role_int: int = secrets.discord_bot_credentials["Focus_Role_ID"]


@tree.command(name="focus_mode_in_x_minutes", description="Gives user focus mode role. FocusRemove to take it away")
async def FocusMode(interaction: discord.Interaction, minutes: int):

    Focus_Role_object = interaction.guild.get_role(Focus_Role_int)

    if minutes > 2880 or minutes < 0:
        await interaction.response.send_message("Please input a number of minutes that is between 1 and 2880",
                                                ephemeral=True)

    if minutes == 60:
        hours = minutes / 60
        await interaction.response.send_message(f"You will now be in focus mode for {hours} hour!",
                                                ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(f"Sucessfully given {Focus_Role_object.mention} to {interaction.user.mention}")

    if minutes % 60 == 0 and minutes >= 120:
        hours = minutes / 60
        await interaction.response.send_message(f"You will now be in focus mode for {hours} hours!",
                                                ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(f"Sucessfully given {Focus_Role_object.mention} to {interaction.user.mention}")

    elif minutes % 60 != 0 and minutes == 1:
        await interaction.response.send_message(f"You will now be in focus mode for {minutes} minute!",
                                                ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(f"Sucessfully given {Focus_Role_object.mention} to {interaction.user.mention}")

    elif minutes % 60 != 0 and minutes != 1:
        await interaction.response.send_message(f"You will now be in focus mode for {minutes} minutes!",
                                                ephemeral=True)
        await interaction.user.add_roles(Focus_Role_object)
        print(f"Sucessfully given {Focus_Role_object.mention} to {interaction.user.mention}")


TOKEN = secrets.discord_bot_credentials["API_Key"]
client.run(TOKEN)
